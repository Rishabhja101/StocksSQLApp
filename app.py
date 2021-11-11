from flask import flash, Flask, redirect, render_template, request
import mysql.connector
import csv
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


    cursor.execute('SELECT TickerSymbol, ROUND(100 * (ClosePrice - OpenPrice) /  OpenPrice, 2) AS PercentChange FROM Stocks NATURAL JOIN (SELECT * FROM Prices WHERE Date = "0000-00-00") AS t1 ORDER BY PercentChange DESC LIMIT 10')
    top_movers = cursor.fetchall()
    top_movers_html = '<div>'
    for i in range(len(top_movers)):
        top_movers_html += '<div>' + top_movers[i][0] + ' - ' + str(top_movers[i][1]) + '%' + '</div>'
    top_movers_html += '</div>'

    return render_template('all_watchlists.html', user=username, watchlists=list_html, user_name=username, top_movers=top_movers_html)
    

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
    list_html += '<div>Ticker Symbol, Company Name, PE Ratio, EPS, Market Cap</div><br/>'
    for i in range(len(data)):
        list_html += '<div>' + str(data[i]) + '  <button name="remove" type="submit" value='  + listId + '|' + data[i][0] + '>Remove</button></div>'
    list_html += '</form>'

    if len(data) == 0:
        list_html = '<div>This watchlist is currently empty</div>'

    return render_template('watchlist.html', stocks=list_html, listId=listId, userName=userName, listName=listName)

@app.route("/watchlist", defaults={'listId':-1}, methods = ['POST'])
@app.route("/watchlist/<listId>", methods = ['POST'])
def getWatchlistSearch(listId):
    if listId == -1:
        return 'this list does not exist!'

    cursor.execute('SELECT WatchlistUserName, WatchlistName FROM Watchlists WHERE WatchlistId = ' + listId)
    data = cursor.fetchall()
    userName = data[0][0]
    listName = data[0][1]

    cursor.execute('SELECT * FROM Stocks NATURAL JOIN Watchlists NATURAL JOIN WatchlistToTicker WHERE WatchlistId = ' + listId)
    data = cursor.fetchall()
    list_html = '<form method="post" action="/removeStockFromList/' + listId +  '">'
    list_html += '<div>Ticker Symbol, Company Name, PE Ratio, EPS, Market Cap</div><br/>'
    for i in range(len(data)):
        list_html += '<div>' + str(data[i]) + '  <button name="remove" type="submit" value='  + listId + '|' + data[i][0] + '>Remove</button></div>'
    list_html += '</form>'

    if len(data) == 0:
        list_html = '<div>This watchlist is currently empty</div>'


    searches = getSearchResults(request.form['search_bar'])
    searches_html = '<form method="post" action="/addStockToList/' + listId +  '">'
    searches_html += '<div>Ticker Symbol, Company Name, PE Ratio, EPS, Market Cap</div><br/>'
    for i in range(len(searches)):
        searches_html += '<div>' + str(searches[i]) + '  <button name="add" type="submit" value=' + listId + '|' + searches[i][0] + '>Add</button></div>'
    searches_html += '</form>'
    
    if type(searches) != list:
        searches_html = '<div>' + searches + '</div>'

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

@app.route("/test")
def test():
    query = 'SELECT TickerSymbol, ROUND(100 * (ClosePrice - OpenPrice) /  OpenPrice, 2) AS PercentChange FROM Stocks NATURAL JOIN (SELECT * FROM Prices WHERE Date = "0000-00-00") AS t1 ORDER BY PercentChange DESC LIMIT 10'
    print(query)
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    return str(data)

@app.route("/data")
def uploadData():
    # with open('Data/stockdata.csv', newline='') as csvfile:
    #     spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    #     success = 0
    #     failed = 0
    #     for row in spamreader:
    #         raw = (' '.join(row))
    #         tokens = raw.split(',')
    #         # print(tokens)

    #         query = 'INSERT INTO Stocks VALUES ("' + tokens[0] + '", "' + tokens[1] + '", ' + tokens[2] + ', ' + tokens[3] + ', ' + tokens[4] + ')'
    #         # print(query)
    #         try:
    #             cursor.execute(query)
    #             connection.commit()

    #             success += 1
    #             print(success)
    #         except:
    #             failed += 1
    #             print("error", failed)
    # with open('Data/stockdata2.csv', newline='') as csvfile:
    #     spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    #     success = 0
    #     failed = 0
    #     for row in spamreader:
    #         raw = (' '.join(row))
    #         tokens = raw.split(',')
    #         # print(tokens)

    #         query = 'INSERT INTO Prices VALUES ("' + tokens[0] + '", ' + tokens[1] + ', ' + tokens[2] + ', ' + tokens[3] + ', ' + tokens[4] + ')'
    #         # print(query)
    #         try:
    #             cursor.execute(query)
    #             connection.commit()

    #             success += 1
    #             print(success)
    #         except:
    #             failed += 1
    #             print("error", failed)
    with open('Data/stockdata3.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        success = 0
        failed = 0
        for row in spamreader:
            raw = (' '.join(row))
            tokens = raw.split(',')
            # print(tokens)

            query = 'INSERT INTO Company VALUES ("' + tokens[0] + '", "' + tokens[1] + '", ' + tokens[2] + ', ' + tokens[3] + '", "' + tokens[4] + '")'
            # print(query)
            try:
                cursor.execute(query)
                connection.commit()

                success += 1
                print(success)
            except:
                failed += 1
                print(query)
                print("error", failed)
            

    return "done"

if __name__ == "__main__":
    app.run(debug=True)
