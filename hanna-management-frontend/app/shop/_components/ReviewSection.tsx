'use client';

import { useState, useEffect } from 'react';
import { FiStar, FiCheck, FiAlertCircle } from 'react-icons/fi';
import apiClient from '@/app/lib/apiClient';

interface Review {
  id: number;
  reviewer_name: string;
  rating: number;
  comment: string;
  created_at: string;
}

interface ReviewSectionProps {
  productId: number;
  csrfToken: string | null;
}

function Stars({ rating, interactive = false, onRate }: { rating: number; interactive?: boolean; onRate?: (r: number) => void }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <button
          key={i}
          type="button"
          onClick={() => interactive && onRate?.(i)}
          onMouseEnter={() => interactive && setHover(i)}
          onMouseLeave={() => interactive && setHover(0)}
          disabled={!interactive}
          className={`transition ${interactive ? 'cursor-pointer' : 'cursor-default'}`}
        >
          <FiStar
            className={`w-4 h-4 transition-colors ${
              i <= (interactive ? hover || rating : rating)
                ? 'text-orange-400 fill-orange-400'
                : 'text-gray-300'
            }`}
          />
        </button>
      ))}
    </div>
  );
}

export default function ReviewSection({ productId, csrfToken }: ReviewSectionProps) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');

  useEffect(() => {
    apiClient.get(`/crm-api/products/reviews/?product_id=${productId}`)
      .then((res) => { setReviews(Array.isArray(res.data) ? res.data : (res.data.results || [])); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [productId]);

  const avgRating = reviews.length > 0
    ? reviews.reduce((s, r) => s + r.rating, 0) / reviews.length
    : 0;

  const submitReview = async () => {
    if (!name.trim()) { setFormError('Please enter your name.'); return; }
    if (rating === 0) { setFormError('Please select a star rating.'); return; }
    setSubmitting(true); setFormError('');
    try {
      await apiClient.post(
        '/crm-api/products/reviews/',
        { product: productId, reviewer_name: name, reviewer_email: email || null, rating, comment },
        csrfToken ? { headers: { 'X-CSRFToken': csrfToken } } : {}
      );
      setSubmitted(true);
      setShowForm(false);
    } catch {
      setFormError('Failed to submit review. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-6 pt-5 border-t border-purple-100">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-extrabold text-sky-900 uppercase tracking-wider">Customer Reviews</h3>
          {reviews.length > 0 && (
            <div className="flex items-center gap-2 mt-1">
              <Stars rating={Math.round(avgRating)} />
              <span className="text-xs text-gray-500">{avgRating.toFixed(1)} · {reviews.length} review{reviews.length !== 1 ? 's' : ''}</span>
            </div>
          )}
        </div>
        {!submitted && !showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="text-xs font-bold text-sky-600 hover:text-sky-800 border border-sky-200 hover:border-sky-400 px-3 py-1.5 rounded-full transition"
          >
            Write a Review
          </button>
        )}
      </div>

      {submitted && (
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-xl text-sm mb-4">
          <FiCheck className="w-4 h-4 flex-shrink-0" />
          Thanks! Your review is pending approval.
        </div>
      )}

      {showForm && (
        <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 mb-4 space-y-3">
          <h4 className="text-sm font-bold text-sky-900">Your Review</h4>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Rating *</label>
            <Stars rating={rating} interactive onRate={setRating} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Name *</label>
              <input value={name} onChange={(e) => { setName(e.target.value); setFormError(''); }}
                placeholder="Your name" className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Email (optional)</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com" className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Comment</label>
            <textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3}
              placeholder="Share your experience…"
              className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400 resize-none" />
          </div>
          {formError && (
            <p className="text-xs text-red-600 flex items-center gap-1"><FiAlertCircle className="w-3 h-3" />{formError}</p>
          )}
          <div className="flex gap-2">
            <button onClick={submitReview} disabled={submitting}
              className="flex-1 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl font-bold text-sm transition disabled:bg-gray-300">
              {submitting ? 'Submitting…' : 'Submit Review'}
            </button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition">
              Cancel
            </button>
          </div>
        </div>
      )}

      {!loading && reviews.length === 0 && !showForm && (
        <p className="text-sm text-gray-400 italic">No reviews yet — be the first!</p>
      )}

      <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
        {reviews.map((r) => (
          <div key={r.id} className="bg-white border border-gray-100 rounded-xl p-3">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sky-900 text-sm">{r.reviewer_name}</span>
                <Stars rating={r.rating} />
              </div>
              <span className="text-xs text-gray-400">{new Date(r.created_at).toLocaleDateString()}</span>
            </div>
            {r.comment && <p className="text-sm text-gray-600 leading-relaxed">{r.comment}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
