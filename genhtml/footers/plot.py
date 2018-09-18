# use plotly to build a figure and show the ready-to-include HTML
figure = go.Figure(data=[data], layout=layout)
print(offline.plot(figure, output_type='div'))
