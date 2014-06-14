import opml
import common.netutils as netutils
from datetime import datetime
from shownotes.models import Show, Note, TextEntry, UrlEntry, Topic
import re
from BeautifulSoup import BeautifulSoup

number_pattern = re.compile('(\d+)')


def strip_4_bytes(string):
    re_pattern = re.compile(
        u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
    return re_pattern.sub(u'\uFFFD', string)


def opml_from_shownotes(*urls):
    '''
    returns a list of opml files corresponding to the given
    shownote url
    '''
    responses = [r for r in netutils.get_pages(*urls)]
    opmls = [x.url.replace('html', 'opml') for x in responses]
    return opmls


class OpmlSourceError(Exception):
    pass


class OpmlLoader(object):
    def __init__(self, source):
        self.source = source
        try:
            self.data = opml.parse(source)
        except Exception as e:
            raise OpmlSourceError(e)
        try:
            self.number = self._show_number()
            # we need an explicit copy here so we get the unicode str
            self.title = self.data.title[:]
            self.shownotes = self._get_shownotes()
        except ValueError:
            raise ValueError('Bad opml data, no show number')

    def save(self):
        if self.exists():
            show = Show.objects.get(pk=self.number)
            if self.date_modified() > show.last_updated:
                show.delete()
        if not self.exists():
            self._insert_show()
            self._insert_entries()

    def date_modified(self):
        try:
            date_string = self.data.dateModified
            return datetime.strptime(
                date_string, '%a, %d %b %Y %H:%M:%S %Z')
        except ValueError:
            return datetime.fromtimestamp(0)

    def exists(self):
        return Show.objects.filter(pk=self.number).count() == 1

    def _show_number(self):
        match = number_pattern.search(self.data.title[:])
        if match:
            return int(match.group())
        raise ValueError

    def _delete_show(self):
        assert self.exists()
        Show.objects.get(pk=self.number).delete()
        assert not self.exists()

    def _insert_show(self):
        assert not self.exists()
        show = Show(name=self.title, id=self.number,
                    last_updated=self.date_modified())
        show.name = strip_4_bytes(show.name)
        show.save()
        assert self.exists()

    def _get_shownotes(self):
        stack = [self.data]
        while len(stack) > 0:
            data = stack.pop()
            for v in data:
                if (v.text.endswith('Shownotes') or
                        v.text.endswith('Assets')) and len(v) > 0:
                    return v
                elif len(v) > 0:
                    stack.append(v)
        raise ValueError('No shownotes found')

    def _get_topic(self, name):
        if not Topic.objects.filter(name=name).exists():
            topic = Topic(name=name)
            topic.name = strip_4_bytes(topic.name)
            topic.save()
        else:
            topic = Topic.objects.get(name=name)
        return topic

    def _insert_entries(self):
        assert self.exists()
        show = Show.objects.get(pk=self.number)
        shownotes = self._get_shownotes()
        for topic_line in shownotes:
            if len(topic_line) == 0:
                continue
            topic_name = topic_line.text.strip()
            topic = self._get_topic(topic_name)
            for note in topic_line:
                if len(note) == 0:
                    continue
                new_note = Note(
                    show=show, topic=topic,
                    title=note.text.strip())
                new_note.title = strip_4_bytes(new_note.title)
                new_note.save()
                full_text = []
                for entry in note:
                    if hasattr(entry, 'type'):
                        new_entry = UrlEntry(
                            note=new_note,
                            text=entry.text.strip(),
                            url=entry.url)
                        new_entry.url = strip_4_bytes(new_entry.url)
                        new_entry.save()
                    else:
                        full_text.append(entry.text.strip())
                new_entry = TextEntry(
                    note=new_note, text=u'<br>'.join(full_text))
                new_entry.text = strip_4_bytes(new_entry.text)
                new_entry.save()


class HtmlLoader(object):
    def __init__(self, text, number):
        self.soup = BeautifulSoup(text)
        id_matcher = re.compile('.*Shownotes.*')
        shownote_divs = self.soup.findAll(id=id_matcher)
        if len(shownote_divs) == 0:
            raise ValueError('No shownote div found')
        if len(shownote_divs) > 1:
            raise ValueError('Too many shownote divs found')
        shownote_div = shownote_divs[0]
        self.number = number
        self.list_div = shownote_div.find(
            'div', {'class': 'divOutlineList'})
        self.title = self._extract_title()

    def _extract_title(self):
        title_matcher = re.compile('.*[tT]itle')
        title_div = self.soup.find('', {'class': title_matcher})
        if title_div is None:
            return self.number
        return title_div.text

    def save(self):
        assert not Show.exists(self.number)
        show = Show(id=self.number, name=self.title,
                    last_updated=datetime.fromtimestamp(0))
        show.save()

        topics = [e for e in self.list_div.childGenerator()
                  if hasattr(e, 'findChild') and e.text != u'Search']

        i = 0
        while i < len(topics):
            topic_name = topics[i].text
            if not Topic.exists(topic_name):
                topic = Topic(name=topic_name)
                topic.save()
            else:
                topic = Topic.objects.get(name=topic_name)

            notes = topics[i + 1].find('div', {'class': 'divOutlineList'}) \
                .findChildren('p', recursive=False)

            for note_div in notes:
                next_sibling = note_div.findNextSibling()
                if next_sibling is None or next_sibling.name != u'div':
                    continue

                note = Note(show=show, topic=topic, title=note_div.text)
                note.save()

                contents = note_div.findNextSibling('div').findChildren(
                    '', {'class': 'divOutlineItem'})
                text = []
                for content in contents:
                    link = content.findChild('a')
                    if link:
                        UrlEntry(note=note, text=link.text,
                                 url=link['href']).save()
                    else:
                        text.append(content.text)
                TextEntry(note=note,
                          text='<br>'.join(text).replace('\n', '')).save()
            i += 2
