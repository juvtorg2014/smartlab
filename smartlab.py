import os
import requests
import re
import lxml
from bs4 import BeautifulSoup
from datetime import datetime

URL = 'https://smart-lab.ru/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
						 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 '
						 'Safari/537.36 OPR/99.0.0.0'}


def get_url(url, typed):
	if typed == '1':
		r = requests.get(url + '/comment', headers=HEADERS)
		if r.status_code == 400:
			r = requests.get(url + '/comment/', headers=HEADERS)
	else:
		r = requests.get(url=url, headers=HEADERS)
	if r.status_code == 200:
		return r.text
	else:
		exit("Нет доступа к сайту")


def read_page(url) -> list:
	"""Поиск всех страниц комментариев"""
	all_topics = []
	
	soup = BeautifulSoup(get_url(url, '1'), 'lxml')
	titles = soup.find_all('div', class_='topic')
	for title in titles:
		text_post = title.find('a').text.strip()
		link_post = URL[:-1] + title.find('a').get("href")
		
		topics = read_topic(link_post)
		all_topics.append(topics)
	return all_topics


def read_topic(url_post):
	"""Чтение поста с комментариями"""
	topic = {}
	comments = {}
	list_topic = []
	soup = BeautifulSoup(get_url(url_post, '2'), 'lxml')
	try:
		title = soup.find('div', class_='topic').find('h1', class_="title").text.strip()
		titles = title + ' - ' + url_post
		content = soup.find('div', class_='topic').text.strip().replace(u'\xa0', ' ')
		topic[titles] = content
		list_topic.append(topic)
		list_comments = soup.find_all('div', class_='text')
		for comment in list_comments:
			if len(comment.text) > 1:
				author = comment.previous.parent.find('div', class_='author')
				date_comment = author.nextSibling.find(class_='date').text
				comments[author.text + '-' + date_comment] = comment.text.replace(u'\xa0', '\n')
				list_topic.append(comments)
		return list_topic
	except AttributeError as e:
		print(e)


def get_pages_comment(url) -> list:
	"""Поиск всех страниц комментариев"""
	text = 'https://smart-lab.ru'
	resp = get_url(url, "1")
	soup = BeautifulSoup(resp, 'lxml')
	list_pages = []
	how_pages = soup.find_all('a', class_='page gradient last')
	if len(how_pages) < 2:
		list_pages.append(url + '/comment')
		return list_pages
	else:
		first_p = soup.find_all('a', class_='page gradient last')[0].get('href')
		
		example = first_p[:-2]
		last_p = soup.find_all('a', class_='page gradient last')[1].get('href')
		last_pag = last_p.split('/')
		if last_pag[-1] == '':
			last_page = last_pag[-2][4:]
		else:
			last_page = last_pag[-1][4:]
		for item in range(1, int(last_page)):
			list_pages.append(text + example + str(item))
		return list_pages


def get_comments(url) -> list:
	"""Главная функция загрузки комментов"""
	list_pages = get_pages_comment(url)
	if len(list_pages) == 0:
		print("У трейдера нет комментариев!!! Извиняйте !!!")
		return "0"
	
	list_comment = []
	for page in list_pages:
		print(page)
		dict_comment = get_page_comments(page)
		list_comment.append(dict_comment)
	return list_comment


def get_page_comments(page) -> dict:
	"""Поиск всех комментов со страницы"""
	resp = get_url(page, 2)
	soup = BeautifulSoup(resp, 'lxml')
	dict_comment = {}
	comments = soup.find_all('div', class_='comment')
	top_topics = find_topics(comments)
	for it, top in enumerate(top_topics, start=1):
		print(it, ' = ', top)
		content_list = []
		for item, comment in enumerate(comments, start=1):
			topic = comment.find('div', class_='comment-topic')
			if topic:
				new_topic = ' '.join(topic.text.split(' ')[:-1]).upper()
				content = comment.find('div', class_='text').text.strip()
				url_topic = URL[:-1] + comment.find('a').get('href')
				number = 1
				if top == new_topic:
					new_content = re.sub(r'[^-a-zA-Z\d\s\nа-яА-ЯёЁ., ]', '', content).replace(u'\xa0', '')
					new_content = '->' + new_content
					content_list.append(new_content + '\n')
					new_key = str(it) + ' = ' + "\u0332".join(top) + '\t' + url_topic
					dict_comment[new_key] = content_list
					number = + 1
	return dict_comment


def merge_dict(comments) -> dict:
	"""Объединение комментов одинаковых авторов"""
	new_dict = {}
	authors = set()
	comments = sorted(comments)
	for value in comments:
		authors.add(value[0])
	
	authors = sorted(authors)
	
	for author in authors:
		list_authors = []
		for item in comments:
			if author == item[0]:
				list_authors.append(item[1:])
				new_dict[author] = list_authors
	
	return new_dict


def read_posts(url_post) -> dict:
	"""Нахождение URL всех постов и чтение их"""
	main_post = {}
	resp = BeautifulSoup(get_url(url_post, '2'), 'html')
	try:
		title = resp.find('div', class_='topic').text.split('|')[0].strip()
		titles = resp.find_all(attrs={'class': re.compile(r"topic")})
		
		content = resp.find('div', class_='topic').text.split('|')[1].strip().replace(u'\xa0', '')
		post = title + ' -> ' + content
		comments_list = resp.find_all('div', class_='comment_child')
		comment_dict = {}
		comment_list = []
		for item in comments_list:
			comment_author = item.find('div', class_="author").text.strip()
			comment_time = item.find('li', class_='date').text.strip()
			comment = comment_time + ' -> ' + item.find('div', class_='text').text.strip()
			# comment_dict[comment_author] = comment
			comment_list.append([comment_author, comment])
		# Нужно объединить комменты одинаковых авторов
		new_dict = merge_dict(comment_list)
		comment_dict[post] = new_dict
		return comment_dict
	except AttributeError as e:
		print(e)


def get_posts(url, resp) -> list:
	"""Главная функция загрузки постов и комментариев к ним"""
	name_blog = resp.find('div', class_='full-width blog_info').find('h3').text.upper()
	new_path = os.path.join(os.getcwd(), name_blog)
	titles = resp.find_all('div', class_='topic')
	if titles[0].text.strip() == 'Сюда еще никто не успел написать':
		print("У трейдера нет постов!!! Извиняйте !!!")
		return "0"
		
	list_pages = []
	list_posts = []
	list_all_posts = []

	page = resp.find('div', id='pagination').find_all('a', "page gradient last")[1].get('href')
	last_page = page.split('/')[-2][4:]
	url_blog = url + 'blog/'

	if int(last_page) > 1:
		for page in range(1, int(last_page)):
			list_pages.append(url_blog + 'page' + str(page))
	else:
		pages = resp.find('div', class_ = 'pagination1').find_all('a')
		for page in pages[:-1]:
			new_url = URL[:-1] + str(page.get('href'))
			list_pages.append(new_url)
	
	if len(list_pages) > 1:
		for post in list_pages:
			list_post = find_posts(post)
			list_posts += list_post
			print(post)
	else:
		list_post = find_posts(list_pages[0])
		print(list_pages[0])
	
	if not os.path.exists(new_path):
		os.mkdir(new_path)
	
	print('Список адресов всех постов\n')
	
	for post in list_posts:
		print(post)
		responce = requests.get(post)
		if responce.status_code == 200:
			soup = BeautifulSoup(responce.text, 'html.parser')
			try:
				resp = soup.find('div', id='content').prettify('utf-8')
			except Exception as e:
				print('Страница доступна только для зарегистрированных пользователей ')
				print(e)
				continue
			title = soup.find('h1', class_='title').text
			titles = re.sub(r'[^-a-zA-Z0-9а-яА-ЯёЁ., ]', '_', title)
			print(titles)
			new_name = os.path.join(new_path, titles) + '.html'
			with open(new_name, 'wb') as f:
				f.write(resp)
		else:
			print(f'Не доступна страница {post}')
			continue
	return list_all_posts
	
	
	
def find_posts(url) -> list:
	"""Поиск всех постов на странице"""
	list_post = []
	soup = BeautifulSoup(get_url(url, '2'), 'html')
	titles = soup.find_all('div', class_='topic')
	for title in titles:
		url_post = URL[:-1] + title.find('a').get('href')
		list_post.append(url_post)
	return list_post
		


def main(url, resp, typed):
	"""Главная рабочая функция"""
	today = str(datetime.date(datetime.now()))
	soup = BeautifulSoup(resp, 'lxml')
	name_file = url.split('/')[-1]
	name_file_comments = name_file + "_comts" + '_' + today + '.txt'
	name_file_post = name_file + "_posts" + '_' + today + '.txt'
	list_post = []
	if typed == '1':
		list_comments = get_comments(url)
		write_file(name_file_comments, list_comments, typed)
		print(f'Записан файл {name_file_comments}')
	elif typed == '2':
		list_posts = get_posts(url, soup)
		print(f'Записан файлы в папку пользователя')
	else:
		list_posts = get_posts(url, soup)
		list_comments = get_comments(url)
		if len(list_posts) > 1:
			write_file(name_file + "_posts.txt", list_posts, typed)
			print(f'Записан файл {name_file_post}')
		if len(list_comments) > 1:
			write_file(name_file_post, list_comments, typed)
			print(f'Записан файл {name_file_post}')




def find_topics(dict_top) -> set:
	"""Поиск уникальных тем на странице"""
	top_topics = set()
	for top in dict_top:
		topic = top.find('div', class_='comment-topic')
		if topic:
			new_topic = ' '.join(topic.text.split(' ')[:-1])
			top_topics.add(new_topic.upper())
	return top_topics


def get_list_urls(soup) -> list:
	"""Получить список ссылок тем на странице"""
	titles = soup.find_all('div', class_='topic')
	list_urls = []
	for title in titles:
		url_topic = URL + title.find('a')['href']
		list_urls.append(url_topic)
	return list_urls


def write_file(name, content, typed):
	"""Запись всех комментариев трейдера"""
	with open(os.getcwd() + '\\' + name, 'w', encoding='utf-8') as fw:
		if typed == '1':
			for item in content:
				for key, value in item.items():
					fw.writelines('\n')
					fw.writelines(key.upper())
					fw.writelines('\n\n')
					for item in value:
						fw.writelines(item.replace('\n', ""))
					fw.writelines('\n')
		else:
			for post in content:
				if post[0] is not None:
					for key, value in post[0].items():
						fw.writelines('\n')
						title = key.split('->')[0]
						text_post = key.split('->')[1]
						fw.writelines(title.upper())
						fw.writelines('\n')
						fw.writelines(text_post.replace('\n', ''))
						fw.writelines('---------КОММЕНТАРИИ-----------\n')
						fw.writelines('\n')
						for item, comment_author in value.items():
							fw.writelines(str(item.upper()))
							fw.writelines('\n')
							for comment in comment_author:
								fw.writelines(str(comment[0]))
								fw.writelines('\n')
						fw.writelines('\n\n')


if __name__ == '__main__':
	choise = input("Комменты (1) или посты (2) или всё (3)\n")
	if choise in ['1', '2', '3']:
		#trader = input("Выберите каталог трейдера со страницы Смарт-лаба\n")
		#trader_url = URL + 'my/' + trader.split('/')[-2]
		trader_url = 'https://smart-lab.ru/my/renat_vv/'
		answer = get_url(trader_url, choise)
		if answer:
			main(trader_url, answer, choise)
	else:
		print(f"Введено неправильно {choise}")
