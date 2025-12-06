import io, zipfile, xml.etree.ElementTree as ET
from django import forms
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from .models import Quote


def extract_text_from_docx(file_bytes: bytes):
    """
    Return a list of paragraph strings from a .docx file
    without using python-docx or lxml.
    """
    paragraphs = []
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx_zip:
        with docx_zip.open('word/document.xml') as xml_file:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            # Word namespaces
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            for para in root.findall('.//w:p', ns):
                texts = [node.text for node in para.findall('.//w:t', ns) if node.text]
                if texts:
                    paragraphs.append(''.join(texts))
    return paragraphs


class ImportQuotesForm(forms.Form):
    docx_file = forms.FileField(
        label='Select a DOCX file',
        help_text='File should contain one quote per line',
        widget=forms.FileInput(attrs={'accept': '.docx'})
    )
    author = forms.CharField(
        max_length=200,
        help_text='Author for all imported quotes',
        widget=forms.TextInput(attrs={'placeholder': 'Enter author name'})
    )


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'created_at')
    search_fields = ('text', 'author')
    list_filter = ('created_at',)
    change_list_template = 'admin/quotes/quote/change_list.html'
    actions = ['delete_all_quotes']

    def delete_all_quotes(self, request, queryset):
        count = Quote.objects.count()
        if count:
            Quote.objects.all().delete()
            self.message_user(request, f'Successfully deleted {count} quotes.', messages.SUCCESS)
        else:
            self.message_user(request, 'No quotes to delete.', messages.WARNING)
        return redirect('admin:quotes_quote_changelist')

    delete_all_quotes.short_description = 'Delete ALL quotes (irreversible)'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-quotes/',
                self.admin_site.admin_view(self.import_quotes),
                name='import_quotes',
            ),
        ]
        return custom_urls + urls

    def import_quotes(self, request):
        if request.method == 'POST':
            form = ImportQuotesForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    docx_file = request.FILES['docx_file']
                    author = form.cleaned_data['author']
                    raw_bytes = docx_file.read()

                    quotes = []
                    for text in extract_text_from_docx(raw_bytes):
                        t = text.strip()
                        if t:
                            # Remove surrounding quotes if present
                            if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
                                t = t[1:-1]
                            quotes.append(Quote(text=t, author=author))

                    if quotes:
                        Quote.objects.bulk_create(quotes)
                        self.message_user(request, f'Successfully imported {len(quotes)} quotes.', messages.SUCCESS)
                    else:
                        self.message_user(request, 'No quotes found in the document.', messages.WARNING)

                    return redirect('admin:quotes_quote_changelist')

                except Exception as e:
                    self.message_user(request, f'Error processing file: {e}', messages.ERROR)
        else:
            form = ImportQuotesForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Import Quotes from DOCX',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/import_quotes.html', context)
