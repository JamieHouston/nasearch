from shownotes.models import Topic
from django.core.paginator import Paginator, EmptyPage
from haystack.query import SearchQuerySet, SQ
from haystack.inputs import AutoQuery
import math


def topics():
    return [{'text': t.name, 'id': t.id} for t in Topic.objects.all()]


def search(parameters):
    RESULTS_LIMIT = 20
    topics = []
    if 'topics' in parameters:
        topics = [int(t) for t in parameters['topics'].split() if t.isdigit()]
    limit = RESULTS_LIMIT
    if 'results_limit' in parameters:
        limit = math.min(RESULTS_LIMIT, parameters['results_limit'])
    page = 1
    if 'page' in parameters and parameters['page'].isdigit():
        page = int(parameters['page'])
    string = ''
    if 'string' in parameters:
        string = parameters['string']

    response_dict = {'results': [], 'page': 0, 'page_count': 0,
                     'result_count': 0}
    if string == '' and topics == []:
        print response_dict
        return response_dict

    if string == '':
        results = SearchQuerySet().filter(topic_id__in=topics) \
            .order_by('-show_number').order_by('topic_name')
    else:
        results = SearchQuerySet().filter(topic_id__in=topics) \
            .filter(SQ(text=AutoQuery(string)) |
                    SQ(text_entry=AutoQuery(string)))

    response_dict['result_count'] = results.count()
    paginator = Paginator(results, limit)
    print paginator.num_pages
    response_dict['page_count'] = paginator.num_pages
    try:
        paged_results = paginator.page(page)
        response_dict['page'] = page
    except EmptyPage:
        paged_results = []
        response_dict['page'] = 0
    response_dict['results'] = [{'show_number': x.show_number,
                                 'topic_name': x.topic_name,
                                 'title': x.text,
                                 'urls': [url for url in x.url_entries],
                                 'text': x.text_entry}
                                for x in paged_results]
    return response_dict
