import stripe
import os
from datetime import datetime, timedelta
from flask import current_app
from models import db, User, SubscriptionPlan

# Configure Stripe
stripe.api_key = os.environ['STRIPE_SECRET_KEY']

def create_stripe_customer(user):
    """Create a Stripe customer for the user"""
    try:
        customer = stripe.Customer.create(
            email=user.email,
            metadata={'user_id': user.id}
        )
        return customer.id
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error: {str(e)}")
        return None

def create_subscription(user, plan_id):
    """Create a subscription for the user"""
    try:
        plan = SubscriptionPlan.query.get(plan_id)
        if not plan or not plan.is_active:
            return False, "Invalid or inactive plan"

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': plan.stripe_price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='http://localhost:5000/subscription/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:5000/subscription/cancel',
            customer_email=user.email,
            metadata={
                'user_id': user.id,
                'plan_id': plan_id
            }
        )
        
        return True, checkout_session.url
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error: {str(e)}")
        return False, str(e)

def handle_subscription_success(session_id):
    """Handle successful subscription payment"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        user_id = int(session.metadata['user_id'])
        plan_id = int(session.metadata['plan_id'])
        
        user = User.query.get(user_id)
        plan = SubscriptionPlan.query.get(plan_id)
        
        if user and plan:
            user.subscription_type = plan.name
            user.subscription_end_date = datetime.utcnow() + timedelta(days=30 * plan.duration_months)
            db.session.commit()
            return True, "Subscription activated successfully"
            
        return False, "Invalid user or plan"
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error: {str(e)}")
        return False, str(e)

def cancel_subscription(user):
    """Cancel user's subscription"""
    try:
        user.subscription_type = 'free'
        user.subscription_end_date = None
        db.session.commit()
        return True, "Subscription cancelled successfully"
    except Exception as e:
        current_app.logger.error(f"Error cancelling subscription: {str(e)}")
        return False, str(e)
