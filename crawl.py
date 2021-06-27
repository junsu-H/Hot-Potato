from konlpy.tag import Mecab
from newspaper import Article
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize
import numpy as np
import requests
from bs4 import BeautifulSoup
import pymysql
import datetime


class SentenceTokenizer(object):
    def __init__(self):
        self.mecab = Mecab()
        self.stopwords = ['기자', '뉴스']

    def url2sentences(self, url):

        article = Article(url, language='ko')
        article.download()
        article.parse()

        sentences = list(map(str, article.text.split('.')))
        return sentences

    def text2sentences(self, text):
        sentences = list(map(str, text.split('.')))
        return sentences

    def get_nouns(self, sentences):
        nouns = []
        for sentence in sentences:
            if sentence is not '':
                nouns.append(' '.join([noun for noun in
                                       self.mecab.nouns(str(sentence))
                                       if noun not in self.stopwords]))
        return nouns

    def get_jx(self, sentences):
        mecab = Mecab()
        pos = []
        jx = []

        for sentence in sentences:
            pos += mecab.pos(sentence)

        for sentence, morpheme in pos:
            if sentence is not '' and morpheme == 'JX':
                jx.append(sentence)
        return jx


class GraphMatrix(object):
    def __init__(self):
        self.tfidf = TfidfVectorizer()
        self.cnt_vec = CountVectorizer()
        self.graph_sentence = []

    def build_sent_graph(self, sentence):
        tfidf_mat = self.tfidf.fit_transform(sentence).toarray()
        self.graph_sentence = np.dot(tfidf_mat, tfidf_mat.T)
        return self.graph_sentence

    def build_words_graph(self, sentence):
        cnt_vec_mat = normalize(self.cnt_vec.fit_transform(
            sentence).toarray().astype(float), axis=0)
        vocab = self.cnt_vec.vocabulary_
        return np.dot(cnt_vec_mat.T, cnt_vec_mat), {vocab[word]: word
                                                    for word in vocab}


class Rank(object):
    def get_ranks(self, graph, d=0.85):  # d = damping factor
        A = graph
        matrix_size = A.shape[0]
        for id in range(matrix_size):
            A[id, id] = 0  # diagonal 부분을 0으로
            link_sum = np.sum(A[:, id])  # A[:, id] = A[:][id]
            if link_sum != 0:
                A[:, id] /= link_sum
            A[:, id] *= -d
            A[id, id] = 1
        B = (1-d) * np.ones((matrix_size, 1))
        ranks = np.linalg.solve(A, B)  # 연립방정식 Ax = b
        return {idx: r[0] for idx, r in enumerate(ranks)}


class TextRank(object):
    def __init__(self, text):
        self.sent_tokenize = SentenceTokenizer()
        if text[:5] in ('http:', 'https'):
            self.sentences = self.sent_tokenize.url2sentences(text)
        else:
            self.sentences = self.sent_tokenize.text2sentences(text)

        self.nouns = self.sent_tokenize.get_nouns(self.sentences)
        self.graph_matrix = GraphMatrix()
        self.sent_graph = self.graph_matrix.build_sent_graph(self.sentences)
        self.words_graph, self.idx2word = self.graph_matrix.build_words_graph(
            self.nouns)
        self.rank = Rank()
        self.sent_rank_idx = self.rank.get_ranks(self.sent_graph)
        self.sorted_sent_rank_idx = sorted(
            self.sent_rank_idx, key=lambda k: self.sent_rank_idx[k],
            reverse=True)

        self.word_rank_idx = self.rank.get_ranks(self.words_graph)
        self.sorted_word_rank_idx = sorted(
            self.word_rank_idx, key=lambda k: self.word_rank_idx[k],
            reverse=True)

    def summarize(self, sent_num=3):
        summary = []
        index = []
        for idx in self.sorted_sent_rank_idx[:sent_num]:
            index.append(idx)
        index.sort()
        for idx in index:
            summary.append(self.sentences[idx])

        return summary

    def keywords(self, word_num=10):
        rank = Rank()
        rank_idx = rank.get_ranks(self.words_graph)
        sorted_rank_idx = sorted(
            rank_idx, key=lambda k: rank_idx[k], reverse=True)
        keywords = []
        index = []
        for idx in sorted_rank_idx[:word_num]:
            index.append(idx)

            # index.sort()
        for idx in index:
            keywords.append(self.idx2word[idx])
        return keywords


class Crawl(object):
    def get_href(self, start):
        url = 'https://search.naver.com' + \
            '/search.naver?where=news&sm=tab_jum' + \
            '&query=%EC%98%A4%EB%8A%98&sort=0&photo=0&field=0' + \
            '&pd=0&ds=&de=&cluster_rank=0&mynews=0' + \
            '&office_type=0&office_section_code=0' + \
            '&news_office_checked=&nso=so:r,p:all,a:all&start=' + \
            str(start)
        raw = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(raw.text, "html.parser")

        links = soup.find_all('a')

        href = []

        try:
            for a in links:
                href.append(a.attrs['href'])

        except Exception:
            print('href Not Found')
        return list(set(href))


def insert_news(keyword, summary, url):
    try:
        # TODO: change host to your MySQL IP
        conn = pymysql.connect(host='172.18.0.25',
                               user='root', password='news',
                               db='news', charset='utf8')
        try:
            with conn.cursor() as curs:
                sql = 'INSERT INTO news(keyword, summary, url)' + \
                    'VALUES(%s, %s, %s)'
                curs.execute(sql, (keyword, summary, url))
            conn.commit()
        except Exception:
            print("Insert Error")
    except Exception:
        print("change host your MySQL IP")
    finally:
        conn.close()


s = SentenceTokenizer()

c = Crawl()
# 0 -> 1 Page
url_list = c.get_href(0)

# 10 -> 2 Page
# url_list = c.get_href(10)

# 20 -> 3 Page
# url_list = c.get_href(20)

for url in url_list:
    try:
        textrank = TextRank(url)
        keyword = ' '.join(map(str, textrank.keywords(3)))
        summary = '. '.join(map(str, textrank.summarize(3))
                            ).replace('\n\n', '') + '.'

        insert_news(keyword, summary, url)
        print()
        print('keywords: ' + keyword)
        print('summary: ' + summary)
        print('url: ' + url)
        print()
    except Exception:
        print ("News URL Not Found")
