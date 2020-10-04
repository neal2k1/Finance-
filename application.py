import os
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    #Create a tabel that groups the data from transactions
    rows = db.execute("SELECT Symbol, Name, SUM(shares) AS total_shares, Price, SUM(Total) AS Final_Amount FROM transactions WHERE user_id = :user_id GROUP BY Symbol", user_id=session["user_id"])
    holdings = []
    grand_total = 0
    for row in rows:
        holdings.append({
            "Symbol": row["Symbol"],
            "Name": row["Name"],
            "Shares": row["total_shares"],
            "Price": usd(row["Price"]),
            "Total": usd(row["Final_Amount"])
        })
        grand_total += row["Final_Amount"]
    rows = db.execute("SELECT cash FROM users WHERE id=:user_id", user_id=session["user_id"])
    cash_owned = rows[0]["cash"]

    grand_total += cash_owned

    return render_template("portfolio.html", holdings=holdings, cash_owned=usd(cash_owned), grand_total=usd(grand_total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))

        #Check statements for the symbol and shares
        if quote == None:
            return apology("invalid quote symbol", 403)

        shares = int(request.form.get("shares"))

        if shares <= 0:
            return apology("Please provide a positive share number", 403)

        #Query the database to see how much cash a user has
        rows = db.execute("SELECT cash FROM users WHERE id =:user_id", user_id=session["user_id"])

        cash_owned = rows[0]["cash"]

        updated_cash = cash_owned - (shares * quote["price"])
        if updated_cash < 0:
            return apology("cannot afford to buy shares")

        #update the database putting the new cash value into the cash coloumn
        db.execute("UPDATE users SET cash=:updated_cash WHERE id=:user_id", updated_cash=updated_cash, user_id=session["user_id"])
        #Add to transactions and create a table in sqlite3 finance.db for the values to be stored
        db.execute("INSERT INTO transactions(user_id, Symbol, Name, Shares, Price, Total) VALUES(:user_id, :symbol, :name, :shares, :price, :total)", user_id=session["user_id"] ,symbol=request.form.get("symbol"), name=quote["name"], shares=shares, price=quote["price"], total=shares*quote["price"])

        flash("Bought!")

        return redirect("/")

    else:
        return render_template("buy.html")




@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT Symbol, Shares, Price, Transacted FROM transactions WHERE user_id = :user_id", user_id=session["user_id"])
    values = []
    for row in rows:
        values.append({
            "Symbol": row["Symbol"],
            "Shares": row["Shares"],
            "Price": usd(row["Price"]),
            "Transacted": row["Transacted"]
        })

    return render_template("history.html", values=values)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        quote = lookup(request.form.get("symbol"))

        if quote == None:
            return apology("invalid quote symbol", 403)

        return render_template("quoted.html", quote=quote)

    else:
        return render_template("quote.html")




@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        # Create a hash table to link the password to
        hash = generate_password_hash(request.form.get("password"))
        #insert the user and hash value into the database
        new_user_id = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash = hash)

        # check if username is unique
        if not new_user_id:
            return apology("sorry username already taken", 403)
        # Remember which user has logged in
        session["user_id"] = new_user_id

        # Redirect user to home page
        return redirect("/")


    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        quote = request.form.get("symbol")
        stock = lookup(quote)
        shares = int(request.form.get("shares"))

        if shares <= 0:
            return apology("Please provide a positive share number", 403)

        rows = db.execute("SELECT Symbol, SUM(shares) AS total_shares FROM transactions WHERE user_id = :user_id GROUP BY Symbol", user_id=session["user_id"])

        #Check to see if user has stock
        for row in rows:
            if row["Symbol"] == quote:
                if shares > row["total_shares"]:
                    return apology("Not enough shares avaliable to be sold")

        rows = db.execute("SELECT cash FROM users WHERE id =:user_id", user_id=session["user_id"])

        cash_owned = rows[0]["cash"]

        updated_cash = cash_owned + shares * stock["price"]


        #update the database putting the new cash value into the cash coloumn
        db.execute("UPDATE users SET cash=:updated_cash WHERE id=:user_id", updated_cash=updated_cash, user_id=session["user_id"])
        #Add to transactions and create a table in sqlite3 finance.db for the values to be stored
        db.execute("INSERT INTO transactions(user_id, Symbol, Name, Shares, Price, Total) VALUES(:user_id, :symbol, :name, :shares, :price, :total)", user_id=session["user_id"] ,symbol=request.form.get("symbol"), name=stock["name"], shares= -1 * shares, price=stock["price"], total= -1*shares*stock["price"])

        flash("Sold!")
        return redirect("/")


    else:
        rows = db.execute("SELECT Symbol FROM transactions WHERE user_id = :user_id GROUP BY Symbol", user_id=session["user_id"])
        return render_template("sell.html", symbols=[row["Symbol"] for row in rows])


@app.route("/Add_Funds", methods=["GET", "POST"])
def Add_Funds():
    if request.method == "POST":
        Funds = int(request.form.get("Funds"))

        if not Funds:
            return apology("must provide a fund amount", 403)

        elif Funds != int(request.form.get("Confirm")):
            return apology("You must retype the same fund amount to confirm", 403)

        rows = db.execute("SELECT cash FROM users WHERE id =:user_id", user_id=session["user_id"])

        cash_owned = rows[0]["cash"]
        new_cash = cash_owned + Funds

        db.execute("UPDATE users SET cash=:new_cash WHERE id=:user_id", new_cash=new_cash, user_id=session["user_id"])

        flash("Funds Added!")
        return redirect("/")

    else:
        return render_template("Add_Funds.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
