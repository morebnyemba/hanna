"""
Read-only end-to-end check of the WhatsApp reply chain.

Run it inside the backend container when the bot is not replying:

    docker compose exec backend python manage.py diagnose_bot

It walks the chain in the order a message travels -- config -> inbound webhook
-> flow engine -> outbound queue -> Celery -> Meta -- and reports the first
place the chain is broken, so the failure is located rather than guessed at.
Everything here only reads; it sends no WhatsApp messages and changes no state.
"""
import argparse
import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import F, Q
from django.utils import timezone

OK, WARN, BAD, INFO = 'OK', 'WARN', 'FAIL', '--'


def positive_int(value):
    """argparse type for --hours.

    A plain `int` would accept 0 and negatives, which puts the window's start in
    the future: every activity query then returns nothing and the tool cheerfully
    reports a healthy-looking "no activity" while the bot is on fire. A
    diagnostic that can lie about the thing it exists to measure is worse than no
    diagnostic, so reject the input instead.
    """
    try:
        hours = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(f"--hours must be a whole number, got {value!r}")
    if hours < 1:
        raise argparse.ArgumentTypeError(f"--hours must be at least 1, got {hours}")
    return hours


class Command(BaseCommand):
    help = "Diagnose why the WhatsApp bot is not replying (read-only)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours', type=positive_int, default=24,
            help='How far back to look for message activity (default: 24).',
        )
        parser.add_argument(
            '--check-token', action='store_true',
            help='Also call Meta to verify the access token is still valid.',
        )

    # --- output helpers -------------------------------------------------
    def _line(self, status, text):
        colour = {
            OK: self.style.SUCCESS, WARN: self.style.WARNING,
            BAD: self.style.ERROR, INFO: lambda s: s,
        }[status]
        self.stdout.write(f"  [{status:4}] {colour(text)}")

    def _section(self, title):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{title}"))

    # --- main -----------------------------------------------------------
    def handle(self, *args, **options):
        self.hours = options['hours']
        self.since = timezone.now() - timedelta(hours=self.hours)
        self.problems = []
        self.had_inbound = False

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nWhatsApp bot diagnostics -- activity window: last {self.hours}h"
        ))

        # Each section is isolated: this runs in an environment that is by
        # definition broken, so one failing check must not hide the rest --
        # the section that crashes is often not the one holding the answer.
        checks = [
            ("deployed code", lambda: self._check_deployed_code()),
            ("Meta configuration", lambda: self._check_config(options['check_token'])),
            ("inbound", lambda: self._check_inbound()),
            ("flows", lambda: self._check_flows()),
            ("outbound", lambda: self._check_outbound()),
            ("broker/workers", lambda: self._check_broker_and_workers()),
            ("database", lambda: self._check_database()),
        ]
        for name, check in checks:
            try:
                check()
            except Exception as e:
                self._line(BAD, f"Check '{name}' crashed: {type(e).__name__}: {e}")
                self.problems.append(
                    f"The '{name}' check could not complete ({type(e).__name__}: {e}). "
                    "That failure is itself a finding -- it usually means the database "
                    "or broker is unreachable, or migrations have not been applied."
                )

        self._section("VERDICT")
        if not self.problems:
            self.stdout.write(
                "  No broken link found in the chain. If the bot is still silent, the\n"
                "  next place to look is the Meta side: whether the webhook is actually\n"
                "  reaching this server (check nginx access logs for POSTs to the\n"
                "  webhook URL) and whether the number is inside the 24h customer\n"
                "  service window for free-form replies."
            )
        else:
            self.stdout.write(self.style.ERROR(
                f"  {len(self.problems)} problem(s), most likely cause first:\n"
            ))
            for i, p in enumerate(self.problems, 1):
                self.stdout.write(self.style.ERROR(f"   {i}. {p}"))

    # --- 1. is the fix even running? ------------------------------------
    def _check_deployed_code(self):
        self._section("1. Deployed code")
        try:
            from meta_integration import tasks as mt
            has_fix = hasattr(mt, 'ORDERING_WAIT_BUDGET_SECONDS')
        except Exception as e:  # pragma: no cover - defensive
            self._line(BAD, f"Could not import meta_integration.tasks: {e}")
            self.problems.append("The backend code failed to import; see above.")
            return

        if has_fix:
            self._line(OK, "Running code INCLUDES the send-ordering fix.")
        else:
            self._line(BAD, "Running code PREDATES the send-ordering fix.")
            self.problems.append(
                "This container is running the OLD code. The fix is on main but has "
                "not been deployed here -- rebuild and recreate: "
                "`docker compose up -d --build`."
            )

        from django.conf import settings
        threads = os.getenv('ASGI_THREADS')
        self._line(OK if threads else WARN,
                   f"ASGI_THREADS={threads or 'unset (defaults to ~6 threads)'}")
        if not threads:
            self.problems.append(
                "ASGI_THREADS is unset in this container, so the compose change has "
                "not been applied. Recreate the backend container."
            )
        self._line(INFO, f"Broker: {settings.CELERY_BROKER_URL.split('@')[-1]}")

    # --- 2. Meta configuration ------------------------------------------
    def _check_config(self, check_token):
        self._section("2. Meta configuration")
        from meta_integration.models import MetaAppConfig

        configs = MetaAppConfig.objects.filter(is_active=True)
        n = configs.count()
        if n == 0:
            self._line(BAD, "No ACTIVE MetaAppConfig.")
            self.problems.append(
                "No active MetaAppConfig, so the webhook cannot match inbound "
                "messages and nothing can be sent. Activate one in the admin."
            )
            return
        if n > 1:
            self._line(WARN, f"{n} active MetaAppConfigs -- behaviour is ambiguous.")

        cfg = configs.first()
        self._line(OK, f"Active config '{cfg.name}' (phone_number_id={cfg.phone_number_id})")
        for field in ('access_token', 'verify_token'):
            self._line(OK if getattr(cfg, field, None) else BAD, f"{field} is set"
                       if getattr(cfg, field, None) else f"{field} is EMPTY")
            if not getattr(cfg, field, None):
                self.problems.append(f"MetaAppConfig.{field} is empty.")
        if not cfg.app_secret:
            self._line(WARN, "app_secret empty -- webhook signatures are NOT verified.")

        if check_token:
            self._verify_token(cfg)
        else:
            self._line(INFO, "Token not verified (pass --check-token to call Meta).")

    def _verify_token(self, cfg):
        import requests
        url = f"https://graph.facebook.com/{cfg.api_version}/{cfg.phone_number_id}"
        try:
            r = requests.get(url, headers={'Authorization': f'Bearer {cfg.access_token}'},
                             timeout=15)
        except Exception as e:
            self._line(WARN, f"Could not reach Meta to verify the token: {e}")
            return
        if r.status_code == 200:
            self._line(OK, "Access token accepted by Meta.")
        else:
            body = r.text[:200]
            self._line(BAD, f"Meta rejected the token: HTTP {r.status_code} {body}")
            self.problems.append(
                "The Meta access token is not valid (see the error above). Every send "
                "will fail until it is replaced -- this alone stops all replies."
            )

    # --- 3. inbound -------------------------------------------------------
    def _check_inbound(self):
        self._section("3. Inbound (is Meta reaching us?)")
        from conversations.models import Message
        from meta_integration.models import WebhookEventLog

        inbound = Message.objects.filter(direction='in', timestamp__gte=self.since).count()
        self.had_inbound = bool(inbound)
        self._line(OK if inbound else BAD, f"{inbound} inbound message(s) in the window.")
        if not inbound:
            self.problems.append(
                "No inbound messages recorded at all. The webhook is not reaching the "
                "app (or is failing before it saves). Check nginx access logs for POSTs "
                "to the webhook path, and the Meta app's webhook subscription."
            )

        logs = WebhookEventLog.objects.filter(received_at__gte=self.since)
        self._line(INFO, f"{logs.count()} webhook event log(s).")
        for row in logs.values('processing_status').distinct():
            status = row['processing_status']
            count = logs.filter(processing_status=status).count()
            bad = status in ('failed', 'error', 'rejected')
            self._line(BAD if bad else INFO, f"  status '{status}': {count}")
            if bad and count:
                sample = logs.filter(processing_status=status).order_by('-received_at').first()
                self._line(INFO, f"    latest note: {(sample.processing_notes or '')[:160]}")
                self.problems.append(
                    f"{count} webhook event(s) in state '{status}' -- see the note above."
                )
        stuck = logs.filter(processing_status='processing_queued').count()
        if stuck:
            self._line(WARN, f"{stuck} event(s) still 'processing_queued'.")
            self.problems.append(
                f"{stuck} webhook event(s) are stuck at 'processing_queued': they were "
                "handed to Celery but no worker finished them. Check the flow worker."
            )

    # --- 4. flows ---------------------------------------------------------
    def _check_flows(self):
        self._section("4. Flow engine")
        try:
            from flows.models import Flow, ContactFlowState
        except Exception as e:
            self._line(WARN, f"Could not inspect flows: {e}")
            return

        active = Flow.objects.filter(is_active=True)
        self._line(OK if active.exists() else BAD, f"{active.count()} active flow(s).")
        if not active.exists():
            self.problems.append(
                "No active Flow, so no inbound message can trigger a reply. Activate "
                "the main-menu flow in the admin."
            )
        for f in active[:10]:
            self._line(INFO, f"  '{f.name}'")

        stale = ContactFlowState.objects.filter(
            last_updated_at__lt=timezone.now() - timedelta(hours=24)
        ).count()
        if stale:
            self._line(WARN, f"{stale} contact(s) parked in a flow state older than 24h.")

    # --- 5. outbound -------------------------------------------------------
    def _check_outbound(self):
        self._section("5. Outbound (are replies being produced and sent?)")
        from conversations.models import Message

        out = Message.objects.filter(direction='out', timestamp__gte=self.since)
        total = out.count()
        self._line(OK if total else BAD, f"{total} outgoing message(s) in the window.")

        if total:
            for status in ('pending_dispatch', 'sent', 'delivered', 'read', 'failed'):
                count = out.filter(status=status).count()
                if not count:
                    continue
                level = BAD if status in ('failed', 'pending_dispatch') else OK
                self._line(level, f"  {status}: {count}")
        elif self.had_inbound:
            self.problems.append(
                "Inbound messages arrived but the bot produced NO outgoing messages: "
                "the flow engine is not generating replies. Check the flow worker's "
                "logs for process_flow_for_message_task."
            )
        else:
            # No replies is the expected consequence of no inbound, not a
            # separate fault -- saying otherwise sends you down a false trail.
            self._line(INFO, "  (expected: nothing came in to reply to)")

        # The two checks below run even when the window above was empty, and are
        # deliberately NOT bounded by self.since. `out` filters on when a message
        # was CREATED, but these ask when its status last changed -- and the worst
        # cases fall outside the creation window precisely because they are the
        # worst. A message wedged in 'pending_dispatch' for three days is the most
        # diagnostic thing on this whole report, and a creation-time filter would
        # hide it: the longer it has been stuck, the less likely it is to be
        # reported, and an empty window would skip the check altogether.
        self._check_stuck_and_failed(Message)

    def _check_stuck_and_failed(self, Message):
        from django.db.models import F, Q

        stuck = Message.objects.filter(
            direction='out', status='pending_dispatch',
            timestamp__lt=timezone.now() - timedelta(minutes=10),
        )
        stuck_count = stuck.count()
        if stuck_count:
            oldest = stuck.order_by('timestamp').first()
            age = timezone.now() - oldest.timestamp
            self._line(BAD, f"  {stuck_count} stuck in 'pending_dispatch' "
                            f"(oldest {age.days}d {age.seconds // 3600}h old)")
            self.problems.append(
                f"{stuck_count} message(s) have sat in 'pending_dispatch' for over 10 "
                f"minutes (oldest: {age.days}d {age.seconds // 3600}h). They were created "
                "but the msg_sending worker never picked them up -- the worker is down, "
                "or the broker lost the task."
            )

        # Keyed on the status transition, not creation: a message sent two days
        # ago that failed ten minutes ago is current news. status_timestamp is
        # null on older rows, so fall back to creation time for those.
        failed = Message.objects.filter(direction='out', status='failed').filter(
            Q(status_timestamp__gte=self.since)
            | Q(status_timestamp__isnull=True, timestamp__gte=self.since)
        ).order_by(F('status_timestamp').desc(nulls_last=True), '-timestamp')
        failed_count = failed.count()
        if failed_count:
            self._line(BAD, f"  {failed_count} failed recently; most recent:")
            for m in failed[:3]:
                self._line(INFO, f"    #{m.id}: {str(m.error_details)[:200]}")
            self.problems.append(
                f"{failed_count} outgoing message(s) failed -- the error details above say "
                "why (a Meta error code here is usually the whole answer)."
            )

    # --- 6. broker + workers ----------------------------------------------
    def _check_broker_and_workers(self):
        self._section("6. Broker and Celery workers")
        from whatsappcrm_backend.celery import app

        # Queue depths, straight from Redis.
        try:
            import redis
            from django.conf import settings
            client = redis.Redis.from_url(settings.CELERY_BROKER_URL,
                                          socket_connect_timeout=5, socket_timeout=5)
            client.ping()
            self._line(OK, "Broker reachable.")
            info = client.info('memory')
            used, maxmem = info.get('used_memory', 0), info.get('maxmemory', 0)
            if maxmem:
                pct = used / maxmem * 100
                self._line(BAD if pct > 90 else (WARN if pct > 75 else OK),
                           f"Redis memory {used/1e6:.0f}MB / {maxmem/1e6:.0f}MB ({pct:.0f}%)")
                if pct > 90:
                    self.problems.append(
                        "Redis is nearly full. With maxmemory-policy noeviction, writes "
                        "are being rejected, so tasks cannot be queued. Raise maxmemory."
                    )
            policy = client.config_get('maxmemory-policy') if hasattr(client, 'config_get') else {}
            if policy:
                p = policy.get('maxmemory-policy')
                self._line(OK if p == 'noeviction' else BAD, f"maxmemory-policy={p}")
                if p and p != 'noeviction':
                    self.problems.append(
                        f"Redis maxmemory-policy is '{p}', not 'noeviction'. Queued Celery "
                        "tasks can be evicted silently, which stops replies with no error. "
                        "The redis.conf fix has not been applied -- recreate the container."
                    )
            for q in ('celery', 'whatsapp', 'msg_sending', 'flow_processing', 'cpu_heavy'):
                depth = client.llen(q)
                self._line(WARN if depth > 100 else INFO, f"  queue '{q}': {depth} waiting")
                if depth > 100:
                    self.problems.append(
                        f"Queue '{q}' has {depth} tasks backed up -- its worker is not "
                        "keeping up or is down."
                    )
        except Exception as e:
            self._line(BAD, f"Broker check failed: {e}")
            self.problems.append(
                f"Could not reach the Celery broker ({e}). With the broker down nothing "
                "is queued and the bot cannot reply."
            )

        # Live workers.
        try:
            replies = app.control.inspect(timeout=5).active_queues() or {}
        except Exception as e:
            self._line(WARN, f"Could not inspect workers: {e}")
            return
        if not replies:
            self._line(BAD, "No Celery workers responded.")
            self.problems.append(
                "No Celery worker responded to inspect. If the workers are down, inbound "
                "messages are recorded but no reply is ever generated or sent."
            )
            return

        consumed = set()
        for worker, queues in replies.items():
            names = sorted(q['name'] for q in queues)
            consumed.update(names)
            self._line(OK, f"{worker} -> {', '.join(names)}")
        for required in ('msg_sending', 'flow_processing'):
            if required not in consumed:
                self._line(BAD, f"NOTHING is consuming '{required}'.")
                self.problems.append(
                    f"No running worker consumes '{required}'. Tasks routed there are "
                    "queued forever, so the bot never replies."
                )

    # --- 7. database -------------------------------------------------------
    def _check_database(self):
        self._section("7. Database")
        try:
            with connection.cursor() as c:
                c.execute("SELECT 1")
                if connection.vendor == 'postgresql':
                    c.execute("SELECT count(*) FROM pg_stat_activity")
                    used = c.fetchone()[0]
                    c.execute("SHOW max_connections")
                    limit = int(c.fetchone()[0])
                    pct = used / limit * 100
                    self._line(BAD if pct > 90 else (WARN if pct > 75 else OK),
                               f"connections {used}/{limit} ({pct:.0f}%)")
                    if pct > 90:
                        self.problems.append(
                            "Postgres is close to max_connections; new connections will "
                            "be refused, which takes down workers and the web tier alike."
                        )
                else:
                    self._line(OK, f"Database reachable ({connection.vendor}).")
        except Exception as e:
            self._line(BAD, f"Database check failed: {e}")
            self.problems.append(f"Database is not reachable ({e}).")
