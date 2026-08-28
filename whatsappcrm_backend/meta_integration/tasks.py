# whatsappcrm_backend/meta_integration/tasks.py

import logging
import tempfile
import os
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .utils import send_whatsapp_message, send_read_receipt_api, download_whatsapp_media
from .models import MetaAppConfig
from .signals import message_send_failed
from conversations.models import Message, Contact # To update message status
from products_and_services.models import Product
from .catalog_service import MetaCatalogService


logger = logging.getLogger(__name__)

# How long send_whatsapp_message_task will hold a message back to preserve
# ordering before giving up on ordering and sending it anyway. Generous enough to
# cover a flow that replies with a long burst of messages, bounded so a contact's
# queue can never wedge. See the gate in send_whatsapp_message_task.
ORDERING_WAIT_BUDGET_SECONDS = 120
# Retry ceiling used only while waiting on ordering (3s apart). Sized to outlast
# ORDERING_WAIT_BUDGET_SECONDS so the wall-clock deadline is what ends the wait.
ORDERING_WAIT_MAX_RETRIES = 60
# How long to keep retrying the actual Meta API call for a message before giving
# up and marking it failed. Also wall-clock, for the reason given at its use site.
SEND_RETRY_BUDGET_SECONDS = 300
# Retry ceiling for the send path. It must be an explicit number, NOT None:
# Task.retry() resolves `max_retries=None` to the task's own max_retries
# (celery/app/task.py: `max_retries = self.max_retries if max_retries is None
# else max_retries`), i.e. 10 -- so passing None would silently reimpose the very
# counter the wall-clock budget exists to escape, and a message that had spent
# attempts waiting its turn would be failed on its first transient error. Sized
# to outlast both wall-clock budgets combined (ordering can consume up to
# ORDERING_WAIT_MAX_RETRIES, then the send path up to
# SEND_RETRY_BUDGET_SECONDS / default_retry_delay), so the deadline is what ends
# the retries and never this number.
SEND_RETRY_MAX_RETRIES = 200

# Bounded well under the global CELERY_TASK_TIME_LIMIT. This task's only blocking
# call is a requests.post with a 20s timeout, so anything approaching two minutes
# is wedged, not slow -- and on the gevent messaging worker a wedged task holds
# one of only 20 slots for the whole limit. The hard limit is what the gevent
# pool enforces; the soft limit is here for correctness if this task is ever
# moved to a prefork queue.
@shared_task(bind=True, max_retries=10, default_retry_delay=3, queue='msg_sending',
             time_limit=120, soft_time_limit=90)
def send_whatsapp_message_task(self, outgoing_message_id: int, active_config_id: int):
    """
    Celery task to send a WhatsApp message asynchronously.
    Updates the Message object's status based on the outcome.

    Args:
        outgoing_message_id (int): The ID of the outgoing Message object to send.
        active_config_id (int): The ID of the active MetaAppConfig to use for sending.
    """
    
    try:
        outgoing_msg = Message.objects.select_related('contact').get(pk=outgoing_message_id)
        active_config = MetaAppConfig.objects.get(pk=active_config_id)
    except Message.DoesNotExist:
        logger.error(f"send_whatsapp_message_task: Message with ID {outgoing_message_id} not found. Task cannot proceed.")
        return # Cannot retry if message doesn't exist
    except MetaAppConfig.DoesNotExist:
        logger.error(f"send_whatsapp_message_task: MetaAppConfig with ID {active_config_id} not found. Task cannot proceed.")
        # Update message status to failed if config is missing
        if 'outgoing_msg' in locals():
            outgoing_msg.status = 'failed'
            outgoing_msg.error_details = {'error': f'MetaAppConfig ID {active_config_id} not found for sending.'}
            outgoing_msg.status_timestamp = timezone.now()
            outgoing_msg.save(update_fields=['status', 'error_details', 'status_timestamp'])
        return

    if outgoing_msg.direction != 'out':
        logger.warning(f"send_whatsapp_message_task: Message ID {outgoing_message_id} is not an outgoing message. Skipping.")
        return

    # Avoid resending if already sent successfully or in a final failed state without retries
    if outgoing_msg.wamid and outgoing_msg.status == 'sent':
        logger.info(f"send_whatsapp_message_task: Message ID {outgoing_message_id} (WAMID: {outgoing_msg.wamid}) already marked as sent. Skipping.")
        return
    # Give up on a message whose send budget has run out. This is keyed to the
    # same wall-clock deadline the retry path uses, not to self.request.retries:
    # that counter is shared with the ordering gate below, so a retry-count check
    # here would abandon a message that had merely spent its attempts *waiting
    # its turn* rather than failing to send.
    if (outgoing_msg.status == 'failed'
            and timezone.now() >= outgoing_msg.timestamp + timedelta(seconds=SEND_RETRY_BUDGET_SECONDS)):
        logger.warning(
            f"send_whatsapp_message_task: Message ID {outgoing_message_id} already failed and its "
            f"{SEND_RETRY_BUDGET_SECONDS}s send budget is exhausted. Skipping."
        )
        return

    # --- Sequential delivery gate ---
    # Hold a message back while an earlier message to the same contact is still
    # pending dispatch, or was sent so recently that its delivery receipt has not
    # landed yet, so replies arrive in the order the flow produced them.
    #
    # This gate is best-effort ORDERING, never a delivery decision. It used to be
    # both, and that silently broke the bot: a wait consumed the same
    # `max_retries` budget as a real send failure (10 x 3s = 30s), while the wait
    # itself is CUMULATIVE down the chain -- message 2 waits for 1, message 3
    # waits for 2, and so on. Whenever delivery receipts lagged or stopped
    # arriving (so a message stayed status='sent' for the full 20s window instead
    # of flipping to 'delivered'), message 2 took ~20s and every message from the
    # third onwards exhausted its retries while still waiting and was marked
    # 'failed' WITHOUT EVER BEING SENT. Any flow step that replies with three or
    # more messages therefore lost most of its replies, which reads to a user as
    # "the bot doesn't work".
    #
    # So the wait is now bounded by wall-clock age rather than by retry count,
    # and when the budget runs out the message is SENT anyway (out of order at
    # worst) instead of being failed. An undelivered message is a bug; a
    # slightly-out-of-order one is cosmetic.
    ordering_wait_deadline = outgoing_msg.timestamp + timedelta(seconds=ORDERING_WAIT_BUDGET_SECONDS)
    if timezone.now() < ordering_wait_deadline:
        stale_threshold = timezone.now() - timedelta(seconds=20)
        # Only wait for RECENTLY created pending messages, so one stuck message
        # cannot dam the queue for a contact indefinitely.
        stale_pending_threshold = timezone.now() - timedelta(minutes=1)

        halting_message = Message.objects.filter(
            Q(contact=outgoing_msg.contact),
            Q(direction='out'),
            Q(id__lt=outgoing_msg.id),
            (
                Q(status='pending_dispatch', timestamp__gte=stale_pending_threshold) |
                Q(status='sent', status_timestamp__gte=stale_threshold)
            )
        ).order_by('-id').first()  # Most recent one, for logging

        if halting_message:
            logger.info(
                f"send_whatsapp_message_task: Holding message ID {outgoing_message_id} for contact "
                f"{outgoing_msg.contact.whatsapp_id} behind preceding message ID {halting_message.id} "
                f"(Status: {halting_message.status}, Status Time: {halting_message.status_timestamp}, "
                f"Created: {halting_message.timestamp}). Retrying."
            )
            try:
                # max_retries is raised for the ordering wait specifically: with a
                # 3s delay the default budget of 10 covers only 30s, far short of
                # ORDERING_WAIT_BUDGET_SECONDS, so the deadline above -- not the
                # retry counter -- is what ends the wait.
                raise self.retry(max_retries=ORDERING_WAIT_MAX_RETRIES)
            except self.MaxRetriesExceededError:
                # Fall through and send. Never fail a message for an ordering wait.
                logger.warning(
                    f"send_whatsapp_message_task: Ordering-wait retries exhausted for message "
                    f"{outgoing_message_id}; sending it now (possibly out of order)."
                )
    else:
        logger.warning(
            f"send_whatsapp_message_task: Ordering wait budget "
            f"({ORDERING_WAIT_BUDGET_SECONDS}s) exceeded for message {outgoing_message_id}; "
            f"sending it now (possibly out of order) rather than dropping it."
        )

    logger.info(f"Task send_whatsapp_message_task started for Message ID: {outgoing_message_id}, Contact: {outgoing_msg.contact.whatsapp_id}")

    try:
        # content_payload should contain the 'data' part for send_whatsapp_message
        # and message_type should be the Meta API message type
        if not isinstance(outgoing_msg.content_payload, dict):
            raise ValueError("Message content_payload is not a valid dictionary for sending.")

        api_response = send_whatsapp_message(
            to_phone_number=outgoing_msg.contact.whatsapp_id,
            message_type=outgoing_msg.message_type, # This should be 'text', 'template', 'interactive'
            data=outgoing_msg.content_payload, # This is the actual data for the type
            config=active_config
        )

        if api_response and api_response.get('messages') and api_response['messages'][0].get('id'):
            outgoing_msg.wamid = api_response['messages'][0]['id']
            outgoing_msg.status = 'sent' # Successfully handed off to Meta
            outgoing_msg.error_details = None # Clear previous errors if any
            logger.info(f"Message ID {outgoing_message_id} sent successfully via Meta API. WAMID: {outgoing_msg.wamid}")
        else:
            # Handle failure from Meta API
            error_info = api_response or {'error': 'Meta API call failed or returned unexpected response.'}
            
            # Log Facebook/Meta API errors prominently
            if isinstance(api_response, dict) and 'error' in api_response:
                logger.error(
                    f"FACEBOOK API ERROR for Message ID {outgoing_message_id}: "
                    f"Status Code: {api_response.get('status_code', 'N/A')}, "
                    f"Error Type: {api_response.get('error_type', 'Unknown')}, "
                    f"Details: {api_response.get('error')}"
                )
            else:
                logger.error(f"Failed to send Message ID {outgoing_message_id} via Meta API. Response: {error_info}")
            
            outgoing_msg.status = 'failed'
            outgoing_msg.error_details = error_info
            raise ValueError("Meta API call failed or returned unexpected response.")

    except Exception as e:
        logger.error(f"Exception in send_whatsapp_message_task for Message ID {outgoing_message_id}: {e}", exc_info=True)
        outgoing_msg.status = 'failed'
        outgoing_msg.error_details = {'error': str(e), 'type': type(e).__name__}
        try:
            # Retry on network/transient errors. The budget is wall-clock rather
            # than a retry count because self.request.retries is shared with the
            # ordering gate above -- a message that waited out several ordering
            # retries would otherwise arrive here with its send budget already
            # spent and be failed on its first transient error, never retried.
            send_deadline = outgoing_msg.timestamp + timedelta(seconds=SEND_RETRY_BUDGET_SECONDS)
            if timezone.now() >= send_deadline:
                raise self.MaxRetriesExceededError(
                    f"Send retry budget ({SEND_RETRY_BUDGET_SECONDS}s) exhausted."
                )
            raise self.retry(exc=e, max_retries=SEND_RETRY_MAX_RETRIES)  # Bounded by send_deadline
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for sending Message ID {outgoing_message_id}.")
            # This is a permanent failure. Save the final state and send the notification signal.
            outgoing_msg.status_timestamp = timezone.now()
            outgoing_msg.save(update_fields=['status', 'error_details', 'status_timestamp'])
            message_send_failed.send(sender=self.__class__, message_instance=outgoing_msg)
            return # Exit after handling permanent failure

    # This block is now only reached on success or during retries (before an exception is raised).
    outgoing_msg.status_timestamp = timezone.now()
    outgoing_msg.save(update_fields=['wamid', 'status', 'error_details', 'status_timestamp'])


# A read receipt is one API call with a 15s timeout and is pure courtesy; it must
# never occupy a messaging slot for longer than the message sends it sits beside.
@shared_task(bind=True, max_retries=3, default_retry_delay=10, queue='msg_sending',
             time_limit=60, soft_time_limit=45)
def send_read_receipt_task(self, wamid: str, config_id: int, show_typing_indicator: bool = False):
    """
    Celery task to send a read receipt for a given message ID.
    """
    logger.info(f"Task send_read_receipt_task started for WAMID: {wamid} (Typing: {show_typing_indicator})")
    try:
        active_config = MetaAppConfig.objects.get(pk=config_id)
    except MetaAppConfig.DoesNotExist:
        logger.error(f"send_read_receipt_task: MetaAppConfig with ID {config_id} not found. Task cannot proceed.")
        return  # Cannot retry if config is missing

    try:
        api_response = send_read_receipt_api(wamid=wamid, config=active_config, show_typing_indicator=show_typing_indicator)
        # The read receipt API returns {"success": true}. If the response is None or 'success' is not true, it's a failure.
        if not api_response or not api_response.get('success'):
            # The utility function has already logged the specific error. We raise an exception to trigger a retry.
            raise ValueError(f"API call to send read receipt failed for WAMID {wamid}. Response: {api_response}")

    except Exception as e:
        logger.warning(f"Exception in send_read_receipt_task for WAMID {wamid}, will retry. Error: {e}")
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for sending read receipt for WAMID {wamid}.")


@shared_task(name="meta_integration.download_whatsapp_media_task")
def download_whatsapp_media_task(media_id: str, config_id: int) -> str | None:
    """
    Downloads media from WhatsApp and saves it to a temporary file.
    Returns the path to the temporary file, or None on failure.
    """
    log_prefix = f"[Media Download Task - Media ID: {media_id}]"
    try:
        config = MetaAppConfig.objects.get(pk=config_id)
        # The download_whatsapp_media function returns a tuple or None.
        download_result = download_whatsapp_media(media_id, config)

        if download_result is None:
            logger.error(f"{log_prefix} download_whatsapp_media utility returned None. Download failed.")
            return None
        media_content, mime_type = download_result

        if media_content and mime_type:
            # Determine a file extension from the mime type
            suffix = f".{mime_type.split('/')[-1].split(';')[0]}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(media_content)
                logger.info(f"{log_prefix} Media saved to temporary file: {temp_file.name}")
                return temp_file.name
        else:
            logger.error(f"{log_prefix} Failed to download media content from WhatsApp.")
            return None
    except MetaAppConfig.DoesNotExist:
        logger.error(f"{log_prefix} MetaAppConfig with ID {config_id} not found.") # type: ignore
        return None
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred during media download: {e}", exc_info=True)
        return None

@shared_task
def create_whatsapp_catalog_product(product_id):
    """
    Celery task to create a product in the WhatsApp catalog.
    """
    try:
        product = Product.objects.get(id=product_id)
        service = MetaCatalogService()
        response = service.create_product_in_catalog(product)
        product.whatsapp_catalog_id = response.get("id")
        product.save(update_fields=["whatsapp_catalog_id"])
        logger.info(f"Product {product.name} created in WhatsApp catalog with ID {product.whatsapp_catalog_id}")
    except Product.DoesNotExist:
        logger.error(f"Product with ID {product_id} not found.")
    except Exception as e:
        logger.error(f"Failed to create product {product_id} in WhatsApp catalog: {e}")

@shared_task
def update_whatsapp_catalog_product(product_id):
    """
    Celery task to update a product in the WhatsApp catalog.
    """
    try:
        product = Product.objects.get(id=product_id)
        service = MetaCatalogService()
        service.update_product_in_catalog(product)
        logger.info(f"Product {product.name} updated in WhatsApp catalog.")
    except Product.DoesNotExist:
        logger.error(f"Product with ID {product_id} not found.")
    except Exception as e:
        logger.error(f"Failed to update product {product_id} in WhatsApp catalog: {e}")

@shared_task
def delete_whatsapp_catalog_product(product_id):
    """
    Celery task to delete a product from the WhatsApp catalog.
    """
    try:
        product = Product.objects.get(id=product_id)
        service = MetaCatalogService()
        service.delete_product_from_catalog(product)
        logger.info(f"Product {product.name} deleted from WhatsApp catalog.")
    except Product.DoesNotExist:
        logger.error(f"Product with ID {product_id} not found.")
    except Exception as e:
        logger.error(f"Failed to delete product {product_id} from WhatsApp catalog: {e}")
