import flask
from dash import Dash
import dash_html_components as html
from dash.dependencies import Input, Output

server = flask.Flask(__name__)
app = Dash(__name__, server=server)

app.layout = html.Div([
    html.Button('Open Folder Picker', id='open-folder-picker-button'),
    html.Div(id='folder-picker'),
    html.Div(id='selected-folder')
])


@app.callback(
    Output('folder-picker', 'children'),
    [Input('open-folder-picker-button', 'n_clicks')]
)
def open_folder_picker(n_clicks):
    if n_clicks is None:
        return None
    else:
        return html.Div([
            html.Script('''
                // JavaScript code to open a folder picker and send the selected folder to your Flask route.
                let input = document.createElement('input');
                input.type = 'file';
                input.webkitdirectory = true;
                input.onchange = function() {
                    let folder = input.files[0].webkitRelativePath.split("/")[0];
                    fetch("/selected-folder", {
                        method: "POST",
                        body: JSON.stringify({folder: folder}),
                        headers: {"Content-Type": "application/json"}
                    });
                };
                input.click();
            ''')
        ])


@server.route('/selected-folder', methods=['POST'])
def selected_folder():
    data = flask.request.json
    print(data['folder'])  # or do whatever you need with the selected folder
    return flask.jsonify({})


if __name__ == '__main__':
    app.run_server(debug=True)
