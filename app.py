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

def getSearchResults(keyword):
    cursor.execute("SELECT * FROM Stocks WHERE TickerSymbol LIKE \"" + keyword + "%\" OR CompanyName LIKE \"" + keyword + "%\"")
    data = cursor.fetchall()

    if len(data) == 0:
        cursor.execute("SELECT * FROM Stocks WHERE TickerSymbol LIKE \"%" + keyword + "%\" OR CompanyName LIKE \"%" + keyword + "%\"")
        data = cursor.fetchall()
    
    if len(data) == 0:
        data = "no stocks matching: \"" + str(keyword) + "\""

    return data


@app.route("/")
def main():
    # "main"
    return "Hi there!"

@app.route("/search")
def search():
    return render_template('search.html')

@app.route("/search", methods = ['POST'])
def handle_search():
    text = request.form['search_bar']
    data = getSearchResults(text)

    format = "<div>"
    for i in range(len(data)):
        format += '<div>' + str(data[i]) + '  <button type="submit" value=' + data[i][0] + '>Select</button></div>'
    format += "</div>"
    return render_template('search.html', search_results = format)


@app.route("/watchlists", defaults={'username':'User'})
@app.route("/watchlists/<username>")
def getAllWatchlists(username):
    cursor.execute('SELECT WatchlistName, COUNT(TickerSymbol) FROM Watchlists LEFT JOIN WatchlistToTicker ON (Watchlists.WatchlistId = WatchlistToTicker.WatchlistId) WHERE WatchlistUserName = "' + username + '" GROUP BY Watchlists.WatchlistId;')
    data = cursor.fetchall()

    cursor.execute('SELECT * FROM Watchlists LEFT JOIN WatchlistToTicker ON (Watchlists.WatchlistId = WatchlistToTicker.WatchlistId) WHERE WatchlistUserName = "' + username + '" GROUP BY Watchlists.WatchlistId;')
    ids = cursor.fetchall()

    list_html = '<form method="post" action="/watchlists">'
    for i in range(len(data)):
        list_html += '<div>' + str(data[i]) + '  <button name="button" type="submit" value="remove|'  + str(ids[i][0]) + '">Remove</button><button name="button" type="submit" value="view|' + str(ids[i][0]) + '">View</button></div>'
    list_html += '</form>'

    if len(data) == 0:
        list_html = '<div>You do not have any Watchlists yet.</div>'

    return render_template('all_watchlists.html', user=username, watchlists=list_html, user_name=username)
    

@app.route("/watchlists", defaults={'username':'User1'}, methods = ['POST'])
@app.route("/watchlists/<username>", methods = ['POST'])
def removeWatchlist(username):
    data = request.form["button"].split('|')
    id = data[1]
    print(id)
    print(data)
    if data[0] == 'remove':
        cursor.execute('DELETE FROM WatchlistToTicker WHERE WatchlistId = ' + id)
        cursor.execute('DELETE FROM Watchlists WHERE WatchlistId = ' + id)
        connection.commit()
        return redirect('/watchlists/' + username)    
    elif data[0] == 'add':
        list_name = request.form['new_list_name']
        cursor.execute('INSERT INTO Watchlists VALUES (0, "' + list_name + '", "' + id + '")')
        connection.commit()
        return redirect('/watchlists/' + username)
    elif data[0] == 'view':
        return redirect('/watchlist/' + id)    
    return redirect('/watchlists/' + username)

    

@app.route("/watchlist", defaults={'listId':-1})
@app.route("/watchlist/<listId>")
def getWatchlist(listId):
    if listId == -1:
        return 'this list does not exist!'

    cursor.execute('SELECT WatchlistUserName, WatchlistName FROM Watchlists WHERE WatchlistId = ' + listId)
    data = cursor.fetchall()
    userName = data[0][0]
    listName = data[0][1]

    cursor.execute('SELECT * FROM Stocks NATURAL JOIN Watchlists NATURAL JOIN WatchlistToTicker WHERE WatchlistId = ' + listId)
    data = cursor.fetchall()

    list_html = '<form method="post" action="/removeStockFromList/' + listId +  '">'
    for i in range(len(data)):
        list_html += '<div>' + str(data[i]) + '  <button name="remove" type="submit" value='  + listId + '|' + data[i][0] + '>Remove</button></div>'
    list_html += '</form>'

    return render_template('watchlist.html', stocks=list_html, search_results=[], listId=listId, userName=userName, listName=listName)

@app.route("/watchlist", defaults={'listId':-1}, methods = ['POST'])
@app.route("/watchlist/<listId>", methods = ['POST'])
def getWatchlistSearch(listId):
    if listId == -1:
        return 'this list does not exist!'

    cursor.execute('SELECT WatchlistUserName, WatchlistName FROM Watchlists WHERE WatchlistId = ' + listId)
    data = cursor.fetchall()
    userName = data[0][0]
    listName = data[0][1]

    try:
        text = request.form["add"]
        print(text)
    except:
        print("err")
    print("hiiiiii")

    cursor.execute("SELECT * FROM Stocks NATURAL JOIN Watchlists NATURAL JOIN WatchlistToTicker")
    data = cursor.fetchall()
    list_html = '<form method="post" action="/removeStockFromList/' + listId +  '">'
    for i in range(len(data)):
        list_html += '<div>' + str(data[i]) + '  <button name="remove" type="submit" value='  + listId + '|' + data[i][0] + '>Remove</button></div>'
    list_html += '</form>'


    searches = getSearchResults(request.form['search_bar'])
    searches_html = '<form method="post" action="/addStockToList/' + listId +  '">'
    for i in range(len(searches)):
        searches_html += '<div>' + str(searches[i]) + '  <button name="add" type="submit" value=' + listId + '|' + searches[i][0] + '>Add</button></div>'
    searches_html += '</form>'

    # print(data)
    return render_template('watchlist.html', stocks=list_html, search_results=searches_html, listId=listId, userName=userName, listName=listName)

@app.route("/rename", defaults={'listId':-1}, methods = ['POST'])
@app.route("/rename/<listId>", methods = ['POST'])
def renameWatchlist(listId):
    print(listId)
    new_name = request.form["new_name"]
    cursor.execute('UPDATE Watchlists SET WatchlistName = "' + new_name + '" WHERE WatchlistId = ' + listId)
    connection.commit()
    return redirect('/watchlist/' + listId)


@app.route("/addStockToList", defaults={'listId':-1}, methods = ['POST'])
@app.route("/addStockToList/<listId>", methods = ['POST'])
def AddStockToList(listId):
    data = request.form["add"].split('|')
    listId = data[0]
    ticker = data[1]
    print(listId)
    print(ticker)
    # cursor.execute('INSERT INTO WatchlistToTicker (Watchlist, TickerSymbol) VALUES (0, AAPL);')
    cursor.execute('INSERT INTO WatchlistToTicker VALUES (' + listId + ', "' + ticker + '")')
    connection.commit()
    return redirect('/watchlist/' + listId)

@app.route("/removeStockFromList", defaults={'listId':-1}, methods = ['POST'])
@app.route("/removeStockFromList/<listId>", methods = ['POST'])
def RemoveStockFromList(listId):
    data = request.form["remove"].split('|')
    listId = data[0]
    ticker = data[1]
    print(listId)
    print(ticker)
    cursor.execute('DELETE FROM WatchlistToTicker WHERE WatchlistId = ' + listId + ' AND TickerSymbol = "' + ticker + '";')
    connection.commit()
    return redirect('/watchlist/' + listId)


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
    app.run(debug=True)
