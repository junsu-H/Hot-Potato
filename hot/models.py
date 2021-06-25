# vim hot/models.py

from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt

from hot.routes import app

app.config['MYSQL_HOST'] = '172.17.0.25'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'news'
app.config['MYSQL_DB'] = 'news'
app.config['MYSQL_PORT'] = 3306

# Intialize MySQL
mysql = MySQL(app)

class User(object):
    def login_check(username, password):
        try:
            # bcrypt hash transfer
            password = password.encode('utf-8')
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s', [username])
            account = cursor.fetchone()
            check_password = bcrypt.checkpw(password, account['password'].encode('utf-8'))
            return account, check_password
        except:
            pass

    def get_information(id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', id)
        account = cursor.fetchone()
        return account

    def get_id(username):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id FROM accounts WHERE username = %s', (username, ))
        account = cursor.fetchone()
        return account

    def check_username_exist(username):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username, ))
        account = cursor.fetchone()
        return account

    def account_add(username, password):
        password = (bcrypt.hashpw(password.encode('UTF-8'), bcrypt.gensalt())).decode('utf-8')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO `accounts` (`username`, `password`) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()

    
class News(object):
    def news_all_load():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, keyword, summary, url  FROM news')
        news = cursor.fetchall()
        return news
    
    def select_news(id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, keyword, summary, url  FROM news WHERE id = %s', (id,))
        news = cursor.fetchall()
        return news

    def insert_rating(accounts_id, news_id, rate):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO `rating`(`accounts_id`, `news_id`, `rate`) VALUES (%s, %s, %s)", (accounts_id, news_id, rate))
        mysql.connection.commit()

    def select_rating(accounts_id, news_id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT rate FROM rating WHERE accounts_id = %s AND news_id = %s", (accounts_id, news_id))
        account = cursor.fetchall()
        return account

    def update_rating(accounts_id, news_id, rate):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("UPDATE rating SET rate = %s WHERE accounts_id = %s AND news_id = %s", (rate, accounts_id, news_id))
        mysql.connection.commit()

class Private(object):
    def private_ranking(accounts_id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #sql = select keyword, summary, rate from news join rating on news.id=rating.news_id join accounts on accounts.id = rating.accounts_id order by rate desc\G

        cursor.execute("select DISTINCT keyword, summary, url, rate from news join rating on news.id=rating.news_id join accounts on %s=rating.accounts_id order by rate desc limit 10", (accounts_id,))
        private = cursor.fetchall()
        return private

class Public(object):
    def public_ranking():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        accounts_count = cursor.execute("SELECT COUNT(DISTINCT accounts.id) FROM accounts LEFT JOIN rating ON rate>0")
        select_sql = "SELECT keyword, summary, url, rate/%s FROM news JOIN rating ON news.id=rating.news_id ORDER BY rate desc limit 10;"
        cursor.execute(select_sql, (accounts_count,))
        public = cursor.fetchall()
        return public

