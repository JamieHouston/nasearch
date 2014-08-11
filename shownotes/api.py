import searches
import json
from django.http import HttpResponse
from shownotes.models import Note, UrlEntry, TextEntry


def wrap_json(request, payload):
    """
    return HttpResponse with data correctly formatted for json or jsonp
    depending on the request
    """
    if 'callback' in request.GET:
        return HttpResponse('{}({})'.format(
            request.GET['callback'],
            json.dumps(payload)), content_type='text/javascript')
    else:
        return HttpResponse(json.dumps(payload),
                            content_type='application/json')


def topics(request):
    """
    return a list of paired topic names and ids
    """
    return wrap_json(request, searches.topics())


def search(request):
    """
    perform a search and return the matches
    recognised parameters are: topics, results_limit, page, string
    """
    return wrap_json(request, searches.search(request.GET))


def show(request):
    """
    fetch all shownotes belonging to a specific show number
    """
    return wrap_json(request, searches.show(request.GET))


def note(request):
    """
    retrieve details of a specific note by id
    """
    if 'id' in request.GET and request.GET['id'].isdigit():
        try:
            note = Note.objects.get(id=int(request.GET['id']))
            urls = UrlEntry.get_by_note(note)
            text_entry = TextEntry.get_by_note(note)[0]
            payload = {'show_number': note.show.id,
                       'topic_name': note.topic.name,
                       'title': note.title,
                       'urls': [url.url for url in urls],
                       'text': text_entry.text,
                       'id': note.id}
        except Exception as e:
            print e
            payload = {}
    return wrap_json(request, payload)
