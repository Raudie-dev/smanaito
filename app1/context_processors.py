def plan_context(request):
    """
    Inyecta el plan_obj del usuario logueado en todos los templates.
    Permite usar {{ plan_obj.mod_finanzas }} etc. directamente en los templates.
    """
    plan_obj = None
    user_id = request.session.get('user')
    if user_id:
        try:
            from app1.models import User
            user = User.objects.get(id=user_id)
            plan_obj = user.suscripcion_saas.plan_obj
        except Exception:
            plan_obj = None
    return {'plan_obj': plan_obj}
