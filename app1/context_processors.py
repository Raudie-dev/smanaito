def plan_context(request):
    """
    Inyecta el plan_obj del usuario logueado en todos los templates.
    Permite usar {{ plan_obj.mod_finanzas }} etc. directamente en los templates.
    """
    plan_obj = None
    dias_vencimiento = None
    user_id = request.session.get('user')
    if user_id:
        try:
            from app1.models import User
            import datetime
            user = User.objects.get(id=user_id)
            if hasattr(user, 'suscripcion_saas'):
                suscripcion_obj = user.suscripcion_saas
                plan_obj = suscripcion_obj.plan_obj
                if suscripcion_obj.fecha_vencimiento:
                    delta = suscripcion_obj.fecha_vencimiento - datetime.date.today()
                    dias_vencimiento = delta.days
        except Exception:
            pass
    return {'plan_obj': plan_obj, 'dias_vencimiento': dias_vencimiento}
