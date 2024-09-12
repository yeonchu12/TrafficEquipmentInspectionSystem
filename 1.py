from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/map')
def map_view():
    location = request.args.get('location', 'London')  # 默认显示伦敦
    return render_template('map.html', location=location)

if __name__ == '__main__':
    app.run(debug=True)
