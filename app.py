from flask import Flask, render_template, g, request, flash, redirect, url_for
from db import connect_db, get_db
import datetime


app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "os.env"


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "sqlite_db"):
        g.sqlite_db.close()


@app.route('/', methods=["GET", "POST"])
@app.route('/&day=<day>', methods=["GET", "POST"])
def index(day=None):
    db = get_db()

    if request.method == "POST":
        date = request.form['date'] # YYYY-MM-DD format
        dt = datetime.datetime.strptime(date, "%Y-%m-%d")
        database_date = datetime.datetime.strftime(dt, "%Y%m%d")
        try:
            db.execute("insert into log_date (entry_date) values (?)", [database_date])
            db.commit()
        except Exception as err:
            flash("Você já adicionou o dia de hoje")


    # Todos os dias.
    all_cur = db.execute("select entry_date from log_date order by entry_date desc")
    results = all_cur.fetchall()
    all_date_results = []

    for i in results:
        single_date = {}

        single_date["date"] = i["entry_date"]

        d = datetime.datetime.strptime(str(i["entry_date"]), "%Y%m%d")
        single_date["entry_date"] = datetime.datetime.strftime(d, "%d/%m/%Y")
        all_date_results.append(single_date)

    if not day:
        last_day_cur = db.execute("select log_date.entry_date, sum(food.protein), sum(food.carbos), sum(food.fat), \
            sum(food.calories) from log_date left join food_date on food_date.log_date_id = log_date.id \
            left join food on food.id = food_date.food_id where log_date.entry_date = ?", [all_date_results[0]["date"]])
        last_day_results = last_day_cur.fetchone()

        if last_day_results[0] == None:
            return "Alguma mensagem de erro"

        if last_day_results["sum(food.protein)"] is None:
            day_info = {
                "day": last_day_results["entry_date"],
                "protein": 0,
                "carbos": 0,
                "fat": 0,
                "calories": 0,
            }            
        else:
            day_info = {
                "day": last_day_results["entry_date"],
                "protein": last_day_results["sum(food.protein)"],
                "carbos": last_day_results["sum(food.carbos)"],
                "fat": last_day_results["sum(food.fat)"],
                "calories": last_day_results["sum(food.calories)"],
            }

        return render_template('index.html', all_results=all_date_results, 
                                actual_day=20200223, day_info=day_info)
    else:        
        day = int(day)
        
        # poderia ter utilizado o "sum(food.protein) as protein, eu sei..."
        day_cur = db.execute("select log_date.entry_date, sum(food.protein), sum(food.carbos), sum(food.fat), \
            sum(food.calories) from log_date left join food_date on food_date.log_date_id = log_date.id \
            left join food on food.id = food_date.food_id where log_date.entry_date = ?", [day])
        day_results = day_cur.fetchone()

        if day_results[0] == None:
            return "Alguma mensagem de erro"
        
        if day_results["sum(food.protein)"] is None:
            day_info = {
                "day": day_results["entry_date"],
                "protein": 0,
                "carbos": 0,
                "fat": 0,
                "calories": 0,
            }            
        else:
            day_info = {
                "day": day_results["entry_date"],
                "protein": day_results["sum(food.protein)"],
                "carbos": day_results["sum(food.carbos)"],
                "fat": day_results["sum(food.fat)"],
                "calories": day_results["sum(food.calories)"],
            }
        
        return render_template('index.html', all_results=all_date_results, 
                            actual_day=day, day_info=day_info)


@app.route("/day/<date>", methods=["GET", "POST"])
def day(date):
    db = get_db()
    cur = db.execute("select id, entry_date from log_date where entry_date = ?", [date])
    date_result = cur.fetchone()

    if request.method == "POST":
        add_food = request.form["food_select"]
        if add_food == None:
            flash("Faltou o nome da comida")
    
        db.execute("insert into food_date (food_id, log_date_id) values (?, ?)", [add_food, date_result["id"]])
        db.commit()

    d = datetime.datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
    pretty_date = datetime.datetime.strftime(d, '%d/%m/%Y')

    food_cur = db.execute("select id, name from food")
    food_results = food_cur.fetchall()

    log_cur = db.execute("select food.name, food.protein, food.carbos, food.fat, food.calories from log_date \
        left join food_date on food_date.log_date_id = log_date.id left join food on food.id = food_date.food_id where \
        log_date.entry_date = ?", [date])
    log_results = log_cur.fetchall()

    totals = {}
    totals["protein"] = 0
    totals["carbos"] = 0
    totals["fat"] = 0
    totals["calories"] = 0


    for food in log_results:
        totals["protein"] += food["protein"]
        totals["carbos"] += food["carbos"]
        totals["fat"] += food["fat"]
        totals["calories"] += food["calories"]
    

    return render_template('day.html', entry_date=date_result["entry_date"], pretty_date=pretty_date, 
                            food_results=food_results, log_results=log_results, totals=totals)


@app.route("/foods", methods=["GET", "POST"])
def foods():
    db = get_db()

    if request.method == "POST":
        food_name = request.form["food"]
        protein = int(request.form["protein"])
        carbs = int(request.form["carbs"])
        fat = int(request.form["fat"])
        calories = (protein * 4) + (carbs * 4) + (fat * 9)

        db.execute("insert into food (name, protein, carbos, fat, calories) values(?,?,?,?,?)", \
            [food_name, protein, carbs, fat, calories])
        db.commit()

    cur = db.execute("select name, protein, carbos, fat, calories from food")
    results = cur.fetchall()
    return render_template("food.html", results=results)


if __name__ == "__main__":
    app.run()