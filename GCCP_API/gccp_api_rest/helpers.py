import uuid


def ccp_uuid_generator():
    return f"CCP-{uuid.uuid4().hex[:8].upper()}"