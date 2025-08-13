# salary/app.py

from flask import Flask, render_template, request, jsonify, send_file
from salary_functions import get_salaries, export_to_pdf_arabic, data

app = Flask(__name__)
# تحديث البيانات داخل التطبيق
salary_data_for_ui = {}
for category, ranks in data.items():
    salary_data_for_ui[category] = ranks

@app.route('/')
def index():
    return render_template('index.html', data=salary_data_for_ui)

@app.route('/calculate', methods=['POST'])
def calculate():
    data_from_request = request.json
    results = get_salaries(
        data_from_request.get('category'),
        data_from_request.get('rank'),
        data_from_request.get('degree'),
        data_from_request.get('familyStatus'),
        data_from_request.get('childrenCount'),
        data_from_request.get('seniorChildrenCount'),
        data_from_request.get('isSolidarity')
    )
    if 'error' in results:
        return jsonify(results), 400
    return jsonify(results)

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data_from_request = request.json
    filename = export_to_pdf_arabic(data_from_request)
    if filename:
        return send_file(filename, as_attachment=True, mimetype='application/pdf')
    else:
        return jsonify({'error': 'Failed to generate PDF'}), 500

if __name__ == '__main__':
    app.run(debug=True)