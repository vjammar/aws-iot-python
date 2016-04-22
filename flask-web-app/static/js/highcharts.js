var chart;

$(document).ready(function() {

    // connect to the web socket
    var socket =  io.connect('http://' + document.domain + ':' + location.port + '/chart',  {
      'reconnect': true,
      'reconnection delay': 500,
      'max reconnection attempts': 10
    });

    // event handler for server sent data
    // the data is processed and added to the chart series
    socket.on('log', function(msg) {
        msg = JSON.parse(msg);
        var i = 0;
        var found = false;

        // convert datetime to local
        var utcTime = new Date(Date.parse(msg.createdDateTime))
        var localTime = new Date( utcTime.getTime() - ( utcTime.getTimezoneOffset() * 60000 ) )

        // search series array to see if it already exists
        for (i = 0; i < chart.series.length; i++) {
            if (chart.series[i].name == msg.name) {

                // set found to true
                found = true;
                
                // set shift if longer than 20
                shift = chart.series[i].data.length > 20;
                
                // add the point
                chart.series[i].addPoint([localTime.getTime(), Number(msg.raceTime.toFixed(4))], true, shift);
            }
        }

        // add series if it was not previously found
        if (found == false) {
            chart.addSeries({                        
                name: msg.name,
                data: [[localTime.getTime() , Number(msg.raceTime.toFixed(4))]]
            });
        }

    });
    
    chart = new Highcharts.Chart({
        chart: {
            renderTo: 'data-container',
            defaultSeriesType: 'spline'
        },
        title: {
            text: '100 Meter Dash Records'
        },
        xAxis: {
            type: 'datetime',
            title: {
                text: 'Time'
            },
            labels: {
            formatter: function() {
                return Highcharts.dateFormat('%I:%M:%S %p', this.value);
            }
        }
        },
        yAxis: {
            title: {
                text: 'Completion Time (seconds)'
            }
        },
        tooltip: {
            shared: false,
            formatter: function() {
                var text = '';
                text =  '<b>' + this.series.name + '</b>' + ': ' + Highcharts.numberFormat(this.y, 4) + '(s)'
                        + '<br>' + Highcharts.dateFormat('%I:%M:%S %p', this.x)
                return text;
            }
        },
        series: []
    });
});