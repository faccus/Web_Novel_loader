import requests, lxml.html, os, shutil, string
from lxml import etree
from ebooklib import epub


def setup():
    directory = 'html'
    if os.path.exists(directory):
        shutil.rmtree(directory)

    os.makedirs(directory)


def main(page_url, title):
    directory = 'html'
    setup()

    page = requests.get(page_url)

    with open(directory + '/' + 'home.html', 'w', encoding='utf-8') as writer:
        writer.write(page.text)


    html_page = etree.HTML(page.text)

    page_cover  = html_page.xpath("//img[@class='thumbnail inline-block']")[0]
    cover_link = page_cover.attrib['src']

    actual_cover = requests.get(cover_link, allow_redirects=True)
    extension = actual_cover.headers['Content-type'].split('/')[1]
    cover_path = directory + '/' + 'cover.' + extension

    with open(cover_path, 'wb') as writer:
        writer.write(actual_cover.content)


    page_chapters = html_page.xpath('/html/body/div[3]/div/div/div/div[1]/div/div[2]/div/div[2]/div[5]/div[2]/table/tbody')[0]
    titles   = []
    chapters = []
    for child in page_chapters.getchildren():
        chapters.append('https://www.royalroad.com' + child.attrib['data-url'])
        titles.append(child.getchildren()[0].getchildren()[0].text.strip('\n').strip())


    book = epub.EpubBook()

    book.set_language("en")
    book.set_title(title)
    book.set_cover("cover." + extension, open(cover_path, 'rb').read())
    book.spine.append('cover')


    for i in range(len(chapters)):
        request_chapter_html = requests.get(chapters[i])
        chapter_html = etree.HTML(request_chapter_html.text)
    
        with open(directory + '/' + 'ch' + str(i) + '.html', 'w', encoding='utf-8') as writer:
            writer.write(request_chapter_html.text)
    
    
        page_content = chapter_html.xpath("//div[@class='chapter-inner chapter-content']")[0]
        chap_title = chapter_html.xpath('/html/body/div[3]/div/div/div/div/div[1]/div/div[2]/h1')[0]

        print(titles[i])

        chap = epub.EpubHtml(title=titles[i], file_name="chap_" + str(i) + ".xhtml")
        chap.title = titles[i]

        page_content.insert(0, chap_title)
        chap.set_content(lxml.html.tostring(page_content))

        book.add_item(chap)
        book.spine.append(chap)


    epub_path = ''.join(c for c in title + '.epub' if c in ("-_.() %s%s" % (string.ascii_letters, string.digits)))
        
    if os.path.exists(epub_path):
        os.remove(epub_path)

    epub.write_epub(epub_path, book, {})


title = 'Godclads'
url   = 'https://www.royalroad.com/fiction/59663/godclads-monster-mceldritchcyberpunkprogression'

main(url, title)