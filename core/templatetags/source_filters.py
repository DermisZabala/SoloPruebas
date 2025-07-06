from django import template

register = template.Library()

@register.filter(name='get_id_from_url')
def get_id_from_url(url_string):
    """
    Toma una URL completa y devuelve solo la última parte (el ID).
    Ejemplo: 'https://.../e/abc123xyz' -> 'abc123xyz'
    """
    if not isinstance(url_string, str):
        return ''
    try:
        # Divide la URL por la barra '/' y toma el último trozo
        return url_string.split('/')[-1]
    except (IndexError, AttributeError):
        # Si algo falla (ej. la URL está vacía), devuelve una cadena vacía
        return ''