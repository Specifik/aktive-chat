# core/utils/qr_code.py
import qrcode
import io
import base64
from django.conf import settings
from django.urls import reverse

def generate_qr_code(url, size=200, border=4):
    """
    Generate a QR code for the given URL
    
    Args:
        url (str): The URL to encode in the QR code
        size (int): Size of the QR code in pixels
        border (int): Border size (quiet zone)
        
    Returns:
        BytesIO: Image data in PNG format
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECTION_L,
        box_size=10,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

def generate_qr_code_base64(url, size=200, border=4):
    """
    Generate a QR code as a base64 encoded string for embedding in HTML
    
    Args:
        url (str): The URL to encode in the QR code
        size (int): Size of the QR code in pixels
        border (int): Border size (quiet zone)
        
    Returns:
        str: Base64 encoded PNG image
    """
    img_buffer = generate_qr_code(url, size, border)
    encoded = base64.b64encode(img_buffer.getvalue()).decode('ascii')
    return f"data:image/png;base64,{encoded}"

def generate_session_qr_code(session, request=None):
    """
    Generate a QR code for a shared session
    
    Args:
        session: SharedSession object
        request: HTTP request object (optional)
        
    Returns:
        str: Base64 encoded PNG image
    """
    # Get absolute URL for the session
    if request:
        url = request.build_absolute_uri(session.get_viewer_url())
    else:
        # Fallback to using the configured site domain
        site_domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
        url = f"http://{site_domain}{session.get_viewer_url()}"
    
    return generate_qr_code_base64(url)

def generate_session_qr_code_file(session, request=None):
    """
    Generate a QR code for a shared session as a file-like object
    
    Args:
        session: SharedSession object
        request: HTTP request object (optional)
        
    Returns:
        BytesIO: Image data in PNG format
    """
    # Get absolute URL for the session
    if request:
        url = request.build_absolute_uri(session.get_viewer_url())
    else:
        # Fallback to using the configured site domain
        site_domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')
        url = f"http://{site_domain}{session.get_viewer_url()}"
    
    return generate_qr_code(url)