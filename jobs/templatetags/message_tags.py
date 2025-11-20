from django import template

register = template.Library()

@register.inclusion_tag('adminpanel/partials/messages.html')
def show_messages(messages):
    return {"messages": messages}
