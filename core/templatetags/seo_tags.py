# Archivo: core/templatetags/seo_tags.py (NUEVO)

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def generate_keyword_paragraph(title, content_type):
    """
    Genera un párrafo de palabras clave para SEO, oculto para los usuarios.
    """
    # Normaliza el tipo de contenido para usarlo en las frases
    type_singular = "la película" if "Película" in content_type else "la serie"
    type_generic = "Película" if "Película" in content_type else "Serie"

    # Crea una lista de variaciones de palabras clave
    keywords = [
        f"Ver {title} Online",
        f"{title} Online Gratis",
        f"Disfrutar de {title} gratis",
        f"{title} subtitulada",
        f"Mirar {title} en HD",
        f"{title} completo en español",
        f"Ver {title} en latino",
        f"{title} en castellano",
        f"Ver {title} online gratis",
        f"Ver {title} Gratis",
        f"Ver online {title}",
        f"Descargar {title} por Mega",
        f"Ver {title} sin registrarse",
        f"¿Dónde ver {title}?",
        f"{title} en español",
        f"{title} en línea",
        f"Descargar {title} Online",
        f"{type_generic} {title} completa",
        f"{title} audio latino",
        f"Ver {title} en HD 1080p",
        f"{title} Gratis",
        f"Ver {type_singular} {title} completa",
    ]
    
    # Une todo en un solo párrafo
    paragraph_text = ", ".join(keywords) + "."

    # Envuelve el párrafo en un div con la clase CSS para ocultarlo visualmente.
    # Esta clase ya la tenías en tu CSS original.
    html_output = f'<div class="hidden-for-users"><p>{paragraph_text}</p></div>'
    
    return mark_safe(html_output)