import os
import sys

from .template import Oeye

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from episode.http.httpresponse import HttpResponse


__all__ = ["render_template"]


def render_template(template, context=None, headers=None):
    """Render an html template using the Oeye templete engine"""
    try:
        filters = {"upper": str.upper, "capitalize": str.capitalize, "lower": str.lower}
        with open(template, "r") as f:
            html_content = f.read()
            oeye = Oeye(html_content, filters)

            rendered_template = oeye.render(context or {})

            return HttpResponse().write(rendered_template.encode(), extra_headers=headers, content_type="html")

    except IOError as e:
        raise IOError(e)
    except Exception as e:
        raise Exception(e)
