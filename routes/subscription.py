from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, SubscriptionPlan
from utils.subscription import create_subscription, handle_subscription_success, cancel_subscription

bp = Blueprint('subscription', __name__)

@bp.route('/plans')
@login_required
def plans():
    """Show available subscription plans"""
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    return render_template('subscription/plans.html',
                         plans=plans,
                         current_plan=current_user.subscription_type)

@bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Handle subscription creation"""
    plan_id = request.form.get('plan_id')
    if not plan_id:
        flash('Invalid plan selected', 'error')
        return redirect(url_for('subscription.plans'))
    
    success, result = create_subscription(current_user, int(plan_id))
    if success:
        return redirect(result)  # Redirect to Stripe checkout
    else:
        flash(f'Error creating subscription: {result}', 'error')
        return redirect(url_for('subscription.plans'))

@bp.route('/subscription/success')
@login_required
def subscription_success():
    """Handle successful subscription"""
    session_id = request.args.get('session_id')
    if not session_id:
        flash('Invalid session', 'error')
        return redirect(url_for('subscription.plans'))
    
    success, message = handle_subscription_success(session_id)
    if success:
        flash(message, 'success')
    else:
        flash(f'Error: {message}', 'error')
    return redirect(url_for('subscription.plans'))

@bp.route('/subscription/cancel', methods=['POST'])
@login_required
def cancel():
    """Handle subscription cancellation"""
    success, message = cancel_subscription(current_user)
    if success:
        flash(message, 'success')
    else:
        flash(f'Error: {message}', 'error')
    return redirect(url_for('subscription.plans'))
