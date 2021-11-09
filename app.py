from flask import flash, Flask, redirect, render_template, request
# from flask.globals import request
# from flask_mysqldb import MySQL
# from flaskext.mysql import MySQL
# from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from mysql.connector import Error

def create_server_connection(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database='flask'
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")

    return connection

connection = create_server_connection("localhost", "root", '')
cursor = connection.cursor()

app = Flask(__name__)
# mySQL = MySQL(app)
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_DB'] = 'flask'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# mysql = MySQL(app)
# mysql = SQLAlchemy(app)
# cursor = mysql.connection.cursor()
# cursor.execute()


@app.route("/")
def main():
    # "main"
    return "Hi there!"

@app.route("/search", methods = ['GET'])
def search():
    return render_template('search.html')

@app.route("/searchResults", methods = ['POST'])
def handle_search():
    text = request.form['search_bar']
    print(text)

    query = "SELECT * FROM Stocks WHERE TickerSymbol LIKE \"" + text + "%\" OR CompanyName LIKE \"" + text + "%\""
    print(query)

    cursor.execute("SELECT * FROM Stocks WHERE TickerSymbol LIKE \"" + text + "%\" OR CompanyName LIKE \"" + text + "%\"")
    # cursor.execute('''SELECT * FROM Stocks''')
    data = cursor.fetchall()

    if len(data) == 0:
        cursor.execute("SELECT * FROM Stocks WHERE TickerSymbol LIKE \"%" + text + "%\" OR CompanyName LIKE \"%" + text + "%\"")
        data = cursor.fetchall()
    
    if len(data) == 0:
        data = "no stocks matching: \"" + str(text) + "\""

    print(data)
    return str(data)
 
@app.route("/watchlists")
def getWatchlist():
    cursor.execute("SELECT * FROM Stocks NATURAL JOIN Watchlists NATURAL JOIN WatchlistToTicker")
    data = cursor.fetchall()
    print(data)
    return str(data)
    # return render_template('search.html')


# @app.route("/trendingStocks")
# def search():
#     return render_template('search.html')

@app.route("/stock_search_results")
def stock_search_results(results):

    if not results:
        flash('No results found!')
        return redirect('/')


    return "Hola there!"


if __name__ == "__main__":
    app.run()
