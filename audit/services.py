from .models import AuditLog


def log_action(user, action, module, record_id='', description='', status='success', request=None):
    role = ''
    if user and hasattr(user, 'role') and user.role:
        role = user.role.code
    ip = None
    if request and hasattr(request, 'audit_ip'):
        ip = request.audit_ip
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        role=role,
        action=action,
        module=module,
        record_id=str(record_id) if record_id else '',
        status=status,
        description=description,
        ip_address=ip,
    )
