/* global requirejs _es6 dashboardProps */

/*
 * This file implements the experiment dashboard view.
 *
 * Note that, as of this writing, the main emotion graph uses fake data.
 * It still needs to be integrated with an Emotiv API to get real emotion data.
 *
 */
const React = window.React;
const ReactDOM = window.ReactDOM;
const h337 = window.h337;
const $ = window.$;

requirejs([
  'bluebird',
  'es6-polyfill',
  'bootstrap',
  'whatwg-fetch',
  'lodash',
  'Chartjs',
  'moment',
  'papaparse',
  'radium',
  _es6('components')
], (a, b, c, d, _, Chart, moment, Papa, Radium, Components) => {
  const {Component} = React;
  const {Button, CheckboxInput, Icon, ModalDialog, PopOver} = Components;
  const {update} = React.addons;
  const {Style} = Radium;

  const grey = '#ece7e3';
  const border = `2px solid ${grey}`;

  // The playahead indicator is updated outside of React. It is easier to
  // get good performance this way.
  //
  // The playahead is updated many times per second as media is played.
  // Re-rendering an entire React subtree this often can be prohibitively
  // expensive. Instead, we keep this state as a global variable and manually
  // re-render the playahead when needed.
  //
  // It should be possible to tune the performance of the React rendering
  // enough to make this work well in React, but after having tried to do
  // so I don't think it's worth   it.
  let mediaPosition = 0;
  let currentTime = 0;
  let lastDisplayTime = 0;
  // old media position is used to store the state we come back to after zooming out
  let oldMediaPosition = 0;
  let updatePlayahead = () => {};

  Chart.defaults.global.defaultFontColor = '#bbb';
  Chart.defaults.global.responsive = true;
  Chart.defaults.global.maintainAspectRatio = false;
  Chart.defaults.global.legend.position = 'right';

  // Use external HTML tooltips. The default canvas tooltips get cut off at
  // edges. This implementation is copy-pasted from Chartjs docs, with
  // modifications for style, correctness (!!!), and to make it entirely
  // self-contained in this function.
  //
  //    https://github.com/chartjs/Chart.js/blob/1b277a71e4af83d19a87d09ffeb06841c275fce9/samples/pie-customTooltips.html
  //
  // I was also helped by this modification of the same code:
  //
  //    https://github.com/chartjs/Chart.js/issues/622#issuecomment-249752452
  Chart.defaults.global.tooltips.enabled = false;
  Chart.defaults.global.tooltips.custom = function(tooltip) {
    // Tooltip Element
    var tooltipEl = $('#chartjs-tooltip');
    if (!tooltipEl[0]) {
      $('body').append('<div id="chartjs-tooltip"></div>');
      tooltipEl = $('#chartjs-tooltip');
    }
    // Hide if no tooltip
    if (!tooltip || !tooltip.opacity) {
      tooltipEl.css({
        opacity: 0
      });
      return;
    }

    // Set caret Position
    tooltipEl.removeClass('above below no-transform');
    if (tooltip.yAlign) {
      tooltipEl.addClass(tooltip.yAlign);
    } else {
      tooltipEl.addClass('no-transform');
    }
    // Set Text
    if (tooltip.body) {
      var innerHtml = [
        (tooltip.title || []).join('\n'),
        (tooltip.body[0].lines || []).join('\n')
      ];
      tooltipEl.html(innerHtml.join('\n').replace(/,/g, ', '));
    }
    // Find Y Location on page
    var top = 0;
    if (tooltip.yAlign) {
      top = tooltip.y;
      var offset = (tooltip.caretHeight || 0) + (tooltip.caretPadding || 0);
      if (tooltip.yAlign === 'above') {
        top -= offset;
      } else {
        top += offset;
      }
    }
    var position = $(this._chart.canvas).offset();
    // Display, position, and set styles for font
    var css = {
      opacity: 1,
      width: tooltip.width ? (tooltip.width + 'px') : 'auto',
      left: position.left + tooltip.x + 'px',
      top: position.top + top + 'px',
      fontFamily: tooltip._fontFamily,
      fontSize: tooltip.fontSize,
      fontStyle: tooltip._fontStyle,
      padding: tooltip.yPadding + 'px ' + tooltip.xPadding + 'px',

      position: 'absolute',
      background: 'rgba(0, 0, 0, .7)',
      color: 'white',
      borderRadius: '3px',
      transition: 'all .1s ease',
      pointerEvents: 'none',
      transform: 'translate(-50%, 0)'
    };
    tooltipEl.css(css);
  };

  // ReactChart is a wrapper around Chartjs that lets us think about
  // charts as React components.
  class ReactChart extends Component {
    shouldComponentUpdate(nextProps, nextState) {
      if (nextProps.type !== this.props.type ||
          JSON.stringify(nextProps.options) !==
          JSON.stringify(this.props.options)) {
        return true;
      }
      const {chart} = this;
      if (chart) {
        for (let key of ['datasets', 'labels', 'xLabels', 'yLabels']) {
          chart.data[key] = nextProps.data[key];
        }
        // If datapoints haven't changed, could use render() here, which
        // might be faster.
        //
        // Also, might want to pass 0 as the duration (first argument) to
        // prevent the default animation.
        chart.update();
      }
      return false;
    }

    destroyChart() {
      if (this.chart) {
        this.chart.destroy();
      }
    }

    componentWillUpdate(nextProps, nextState) {
      this.destroyChart();
    }

    componentWillUnmount(nextProps, nextState) {
      this.destroyChart();
    }

    render() {
      const {type, data, options, ...props} = this.props;
      return (
        <canvas {...props} ref={canvas => {
          if (canvas !== null) {
            this.chart = new Chart(canvas, {type, data, options});
          }
        }}>
          Please upgrade your browser to view this chart.
        </canvas>
      );
    }
  }

  // STYLES START
  const flexCenter = {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  };

  const iconStyle = Object.assign({
    width: 42,
    height: 40,
    borderRadius: 3,
    backgroundColor: 'white',
    border: border
  }, flexCenter);

  const clickable = {
    cursor: 'pointer'
  };

  const spaceBetween = {
    display: 'flex',
    justifyContent: 'space-between'
  };

  const thmBackground = {
    backgroundColor: 'white'
  };

  const spaceAround = {
    display: 'flex',
    justifyContent: 'space-around'
  };

  // margin all around small
  const mas = {
    margin: '10px'
  };

  const pam = {
    padding: '20px'
  };

  const freeResponseBorder = 'thin solid #E3E3E3';

  const maxWidth = {
    width: '100%'
  };

  const maxHeight = {
    height: '100%'
  };

  const disabled = {
    backgroundColor: 'lightgrey',
    filter: 'blur(1px)',
    cursor: 'default'
  };

  const dropDownStyle = {
    top: '100%',
    left: 0,
    width: '100%',
    zIndex: 10
  };

  const boxStyle = {
    height: '100%',
    backgroundColor: 'white',
    borderRadius: 7,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '0 32px',
    border: border
  };

  const metrics = [
    {name: 'Engagement', key: 'MAX-ENG'},
    {name: 'Valence', key: 'MAX-VAL'},
    {name: 'Frustration', key: 'MAX-FRU'},
    {name: 'Focus', key: 'MAX-FOC'},
    {name: 'Excitement', key: 'MAX-EXC'}
  ];
  // STYLES END

  // ClickedMarkerModal shows details of an event marker.
  class ClickedMarkerModal extends Component {
    deleteClicked(index) {
      this.props.onDelete(index);
    }
    componentDidMount() {
      window.addToolTip($);
      window.addPopOver($);
      $('[data-toggle="popover"]').popover();
    }
    render() {
      const ts1 = moment.utc(this.props.marker.marker.timestamp1)
        .format("HH:mm:ss.S");
      let text = ts1;
      if (this.props.marker.marker.timestamp2) {
        const ts2 = moment.utc(this.props.marker.marker.timestamp2)
          .format("HH:mm:ss.S");
        text = ts1 + " - " + ts2;
      }
      // TODO get the popover to show up at the location of the click captured in the higher level component
      return (
      <PopOver
        label={'E'}
        title={'Edit event'}
        style={{position: 'absolute', top: `${this.props.location.y}px`, left: `${this.props.location.x}px`}}
        >
          <h3>{text}</h3>
          <p>{this.props.marker.marker.description}</p>
          <Button clear={true} onClick={this.props.onClose}>
            Edit
          </Button>
          <Button clear={true} onClick={this.props.onClose}>
            Cancel
          </Button>
          <Button
            style={{marginTop: "20px"}}
            clear={true}
            onClick={this.deleteClicked.bind(this, this.props.marker.index)}
          >
            Delete
          </Button>
      </PopOver>
      );
    }
  }

  // EmotionGraphContainer holds the state-management logic for EmotionGraph.
  // It is a Container, as in the "Presentational and Container components" pattern.
  // https://medium.com/@dan_abramov/smart-and-dumb-components-7ca2f9a7c7d0#.610esx8ds
  class EmotionGraphContainer extends Component {
    constructor(props) {
      super(props);
      this.state = {
        media: this.props.media,
        currentMediaId: 0,
        metric: metrics[0].key,
        mode: 'all',
        clickedMarker: null,
        zoomedIn: false,
        location: []
      };
    }

    // loadFile loads mock data. It will need to be replaced with a real
    // integration.
    //
    // TODO: replace with real integration
    loadFile(i) {
      fetch(`/dashboard/mock_data/media_${(i % 3) + 1}_mock_data.csv`)
        .then(response => response.text())
        .then(text => Papa.parse(text, {header: true, skipEmptyLines: true}))
        .then(data => {
          this.props.updateMediaForDownload(data.data);
          return this.setState(update(this.state, {
            media: {
              [i]: {
                data: {
                  $set: data.data
                }
              }
            }
          }));
        }
      );
    }

    onDeleteMarker(index) {
      const markers = this.state.media[this.state.currentMediaId].eventMarkers;
      const newMarkers = markers.filter(
        (marker, markerIndex) => markerIndex !== index
      );
      var newMedia = this.state.media;
      newMedia[this.state.currentMediaId].eventMarkers = newMarkers;

      this.setState({
        media: newMedia,
        clickedMarker: null
      });
    }

    eventMarkerClicked() {
      const graph = this;
      return function(evt) {
        const xAxis = this.chart.controller.scales['x-axis-0'];

        const pixelToMs = px => {
          const timeSpan = xAxis.lastTick.diff(xAxis.firstTick);
          const firstTickPixel = xAxis.getPixelForTick(0);
          const pixelSpan = xAxis.getPixelForTick(xAxis.ticks.length - 1) -
            firstTickPixel;
          return (timeSpan * (px - firstTickPixel)) / pixelSpan;
        };

        const msClicked = pixelToMs(evt.offsetX);
        const rectWidth = 14;
        const markerHeight = 22;
        const clickRange = pixelToMs(xAxis.getPixelForTick(0) + rectWidth / 2);

        for (let [index, marker] of
            this.chart.controller.data.datasets[0].eventMarkers.entries()) {
          const rangeLeft = marker.timestamp1 - clickRange;
          const rangeRight = marker.timestamp1 + clickRange;

          const clickedFirstMarker = msClicked >= rangeLeft &&
            msClicked <= rangeRight;

          const clickedSecondMarker = marker.timestamp2 &&
              msClicked >= (marker.timestamp2 - clickRange) &&
              msClicked <= (marker.timestamp2 + clickRange);

          if ((clickedFirstMarker || clickedSecondMarker) &&
              evt.offsetY <= markerHeight) {
            graph.setState({
              location: [evt.x, evt.y],
              clickedMarker: {index, marker}
            });
          }
        }
      };
    }

    componentDidMount() {
      this.state.media.forEach((_, i) => this.loadFile(i));
    }

    toggleZoom() {
      if (this.state.zoomedIn) {
        mediaPosition = oldMediaPosition;
      } else {
        oldMediaPosition = mediaPosition;
        mediaPosition = 0;
      }
      this.setState({zoomedIn: !this.state.zoomedIn});
    }

    render() {
      const {media, currentMediaId, metric, mode, zoomedIn, questionFilters, attributeFilters} = this.state;
      let {experimentName, questions, attributes, responses, groupA, groupB, handleFilterSelect, addGroup, removeGroup} = this.props;
      if (!media.length) {
        return <div>No media in this expmeriment. Emotion data will not be displayed.</div>;
      }
      const currentMedia = media.find(m => m.key === currentMediaId);
      let data;
      let startTime;
      if (zoomedIn) {
        startTime = parseInt(currentMedia.data[0].TimeStamp, 0);
        let endTime = parseInt(_.last(currentMedia.data).TimeStamp, 0);
        let duration = endTime - startTime;
        let lowerBound = startTime + oldMediaPosition * duration;
        let upperBound = startTime + oldMediaPosition * duration + 10;
        if (upperBound > endTime) {
          lowerBound = endTime - 10;
          upperBound = endTime;
        }
        // filter the data down to the 10 secconds from the current time
        data = currentMedia.data
          .filter(item => parseInt(item.TimeStamp, 0) > lowerBound && parseInt(item.TimeStamp, 0) <= upperBound);
      } else {
        data = currentMedia.data;
      }

      // data = data.filter(item => )
      const mediaLength = data.length && (
        parseFloat(data[data.length - 1].TimeStamp) -
        parseFloat(data[0].TimeStamp)
      );
      return <div>
        {this.state.clickedMarker &&
          <ClickedMarkerModal marker={this.state.clickedMarker}
            onClose={_ => this.setState({clickedMarker: null})}
            onDelete={this.onDeleteMarker.bind(this)}
            location={this.state.location}
            />
        }
        <Header
          experimentName={experimentName}
          media={media}
          mediaSelected={currentMediaId}
          mediaLength={mediaLength}
          onEventMarkerAdded={e => {
            const i = media.findIndex(m => m.key === currentMediaId);
            this.setState(update(this.state, {
              media: {
                [i]: {
                  eventMarkers: {
                    $push: [e]
                  }
                }
              }
            }));
            // TODO: Save event to database.
          }}
          onMediaUpdate={m => {
            this.setState({currentMediaId: m.key});
            this.props.setMediaForDownload(m);
          }}
          addGroup={addGroup}
          questions={questions}
          attributes={attributes}
          responses={responses}
          handleFilterSelect={handleFilterSelect}
          groupA={groupA}
          groupB={groupB}
        />
        <EmotionGraph
          data={data}
          metric={metric}
          mode={mode}
          eventMarkers={currentMedia.eventMarkers}
          onMetricUpdate={m => this.setState({metric: m})}
          clickedEventMarker={this.eventMarkerClicked()}
          toggleZoom={this.toggleZoom.bind(this)}
          zoomedIn={this.state.zoomedIn}
          startTime={startTime || null}
          groupA={groupA}
          groupB={groupB}
        />
      </div>;
    }
  }

  // EmotionGraph implements the main line graph of viewers' emotions over time.
  @Radium
  class EmotionGraph extends Component {
    constructor() {
      super();
      this.state = {
        showBarChart: false,
        showLineChart: true
      };
    }
    switchToBarChart() {
      this.setState({
        showBarChart: true,
        showLineChart: false
      });
    }
    convertDataForBarChart(data) {
      // need information about the event markers
      // go group by group to generate new dataset
      return this.props.eventMarkers.map(marker => {
        // if single point marker
        if (marker.timestamp1 && !marker.timestamp2) {
          // grab the one data point closest to timestamp1
          let closestDataPoint = _.minBy(data, item => Math.abs(marker.timestamp1 - this.timeElapsed(item.TimeStamp)));
          return closestDataPoint;
        } else {
          // grab all data in range
          let aggregatedData = data
          .filter(item => this.timeElapsed(item.TimeStamp) >= marker.timestamp1 &&
            this.timeElapsed(item.TimeStamp) <= marker.timestamp2);
          let firstPoint = _.mapValues(aggregatedData[0], item => parseInt(item, 10));
          // return one data point with averaged values
          return aggregatedData.reduce((averagedPoint, item, i) => {
            return _.mapValues(averagedPoint, (val, key) => val + parseInt(item[key], 10) / aggregatedData.length);
          }, firstPoint);
        }
      });
    }
    timeElapsed(epochTime) {
      let m = moment(epochTime, 'X');
      let hourOffset = moment.duration(m.diff(m.clone().startOf('hour')));
      return m.subtract(hourOffset);
    }
    switchToLineChart() {
      this.setState({
        showLineChart: true,
        showBarChart: false
      });
    }
    generateDatasets(data, markers, a, b, metric) {
      // TODO divide the data by group.
      // NEED a way to divide the headset data
      let datasets = [];
      if (a.exists) {
        datasets.push({
          label: 'Group A',
          data: data.map(row => row[metric]),
          eventMarkers: markers,
          borderColor: '#F6CDDE',
          backgroundColor: '#F6CDDE',
          lineTension: 0,
          fill: false
        });
      }
      if (b.exists) {
        datasets.push({
          label: 'Group B',
          data: data.map(row => row[metric]),
          eventMarkers: markers,
          borderColor: '#58afd4',
          backgroundColor: '#58afd4',
          lineTension: 0,
          fill: false
        });
      }
      if (!a.exists && !b.exists) {
        datasets.push({
          label: 'No Group Association',
          data: data.map(row => row[metric]),
          eventMarkers: markers,
          borderColor: '#F6CDDE',
          backgroundColor: '#F6CDDE',
          lineTension: 0,
          fill: false
        });
      }
      return datasets;
    }
    render() {
      const {showLineChart, showBarChart} = this.state;
      const {data, metric, onMetricUpdate, eventMarkers, mode, toggleZoom, zoomedIn, startTime, groupA, groupB} = this.props;
      let zoomIcon = zoomedIn ? 'search-minus' : 'search-plus';
      let hourOffset;
      if (zoomedIn) {
        let m = moment(startTime, 'X');
        hourOffset = moment.duration(m.diff(m.clone().startOf('hour')));
      }
      let dataToGraph = showLineChart ? data : this.convertDataForBarChart(data);
      let datasets = this.generateDatasets(dataToGraph, eventMarkers, groupA, groupB, metric);
      const chartData = {
        labels: dataToGraph.map((row, i) => {
          let m = moment(row.TimeStamp, 'X');
          if (i === 0 && !zoomedIn) {
            hourOffset = moment.duration(m.diff(m.clone().startOf('hour')));
          }
          return m.subtract(hourOffset);
        }),
        datasets: datasets
      };
      const options = {
        legend: {display: false},
        tooltips: {
          callbacks: {
            title: ([item]) => item.xLabel.format('mm:ss.S')
          }
        },
        scales: {
          yAxes: [{
            gridLines: {
              display: false,
              drawBorder: false
            },
            ticks: {
              callback: v => `\u{2015}  ${v}  `
            }
          }],
          xAxes: [{
            type: 'time',
            time: {
              displayFormats: {
                second: 'mm:ss'
              }
            },
            gridLines: {
              display: false,
              drawBorder: false
            }
          }]
        }
      };
      const totalHeight = 350;
      const toolBarHeight = 68;
      return <div style={{
        border: border,
        width: '100%',
        height: totalHeight,
        display: 'flex',
        flexDirection: 'column',
        padding: '0 10px 10px 10px'
      }}>
        <div style={{
          height: toolBarHeight,
          padding: 13,
          display: 'flex',
          justifyContent: 'space-between'
        }}>
          <div className="drop_down" style={{
            height: '100%',
            padding: '16px 19px 16px 26px',
            display: 'inline-flex',
            alignItems: 'center',
            backgroundColor: 'white',
            border: border
          }}>
            {metrics.find(m => m.key === metric).name}
            <Icon style={{marginLeft: 24}} fa="caret-down"/>
            <div className="drop_down-content" style={dropDownStyle}>
              {metrics.map(({name, key}) => <li
                  key={key}
                  onClick={_ => onMetricUpdate(key)}>
                  {name}
              </li>)}
            </div>
          </div>
          <div style={spaceAround}>
            <Icon fa="bar-chart" style={[iconStyle, clickable]} onClick={this.switchToBarChart.bind(this)}/>
            <Icon fa="line-chart" style={[iconStyle, clickable]} onClick={this.switchToLineChart.bind(this)}/>
            <Icon fa={zoomIcon} style={[iconStyle, clickable]} onClick={toggleZoom}/>
          </div>
        </div>
        <div style={{width: '100%', height: totalHeight - toolBarHeight}}>
          {showLineChart ?
            <ReactChart
              type="lineWithEvents"
              data={chartData}
              ref={ref => {
                updatePlayahead = () => {
                  if (ref) {
                    ref.chart.render(0);
                  }
                };
              }}
              options={Object.assign(options, {
                onClick: this.props.clickedEventMarker
              })}
            />
          : null}
          {showBarChart ?
            <VerticalBarChart
              data={chartData} // filter this by time stamp
            /> : null }
        </div>
      </div>;
    }
  }

  // lineWithEvents is a custom ChartJS type, extending the standard line chart.
  //
  // We draw custom elements on the line chart, like event markers and a
  // playahead indicator.
  Chart.controllers.lineWithEvents = Chart.controllers.line.extend({
    draw: function() {
      Chart.controllers.line.prototype.draw.apply(this, arguments);
      const ctx = this.chart.chart.ctx;

      const xAxis = this.chart.scales['x-axis-0'];
      const yAxis = this.chart.scales['y-axis-0'];
      if (!xAxis.ticks || !yAxis.ticks) {
        return;
      }
      const firstTickPixel = xAxis.getPixelForTick(0);
      const pixelSpan = xAxis.getPixelForTick(xAxis.ticks.length - 1) -
        firstTickPixel;
      const msToPixel = ms => {
        const timeSpan = xAxis.lastTick.diff(xAxis.firstTick);
        return firstTickPixel + (ms / timeSpan) * pixelSpan;
      };

      // Render playahead.
      const width = 2;
      ctx.fillStyle = 'black';
      ctx.fillRect(
        firstTickPixel + pixelSpan * mediaPosition - width / 2, // x
        0, // y
        width,
        yAxis.getPixelForTick(yAxis.ticks.length - 1)
      );

      const drawMarker = (ts, num) => {
        ctx.fillStyle = '#ddd';
        ctx.fillRect(
            msToPixel(ts), 0, 1, yAxis.getPixelForTick(yAxis.ticks.length - 1));
        ctx.fillStyle = 'black';
        const width = 14;
        const rectHeight = 17;
        const triHeight = 5;
        const startX = msToPixel(ts) - width / 2;
        const textHeight = rectHeight + triHeight;
        ctx.beginPath();
        ctx.moveTo(startX, 0);
        ctx.lineTo(startX, rectHeight);
        ctx.lineTo(startX + width / 2, rectHeight + triHeight);
        ctx.lineTo(startX + width, rectHeight);
        ctx.lineTo(startX + width, 0);
        ctx.fill();
        const text = "E" + num;
        ctx.strokeText(text, startX, rectHeight);
      };

      for (let [index, marker] of
          this.chart.data.datasets[0].eventMarkers.entries()) {
        if (marker.timestamp1)
          drawMarker(marker.timestamp1, index + 1);
        if (marker.timestamp2)
          drawMarker(marker.timestamp2, index + 1);
      }
    }
  });

  // Lifted this directly from experiment_view. Requirejs makes it difficult to share components
  class QuestionViewFilter extends Component {
    constructor(props) {
      super(props);
      this.state = {
        selected: {},
        selectedAnswers: [],
        inputVal: ""
      };
    }

    addSelectedMultiple(i) {
      let selected = this.state.selected;
      selected[i] = !selected[i];
      const selectedAnswers = Object.keys(this.state.selected).map(x => {
        return this.props.element.answers[x];
      });
      this.setState({
        selected: selected,
        selectedAnswers: selectedAnswers
      });
    }

    multipleSelect(text, answers) {
      const choices = answers.map((answer, i) => {
        return (
          <div key={i} className="standalone_input_box check_input center_element">
            <input id={answer + i} type="checkbox" name="answer" value={answer} onChange={this.addSelectedMultiple.bind(this, i)} />
            <label htmlFor={answer + i}>{answer}</label>
          </div>
        );
      });

      return (
            <div>
                <h1>{text}</h1>
                <h3>Choose all that apply</h3>
                <div style={{marginTop: "25px"}}>
                    {choices}
                </div>
            </div>
      );
    }

    addSelectedSingle(i) {
      const selected = {};
      selected[i] = true;
      const selectedAnswers = Object.keys(selected).map(x => {
        return this.props.element.answers[x];
      });
      this.setState({
        selected: selected,
        selectedAnswers: selectedAnswers
      });
    }

    singleSelect(text, answers) {
      const choices = answers.map((answer, i) => {
        return (
                <div key={i} className="standalone_input_box radio_input center_element">
                    <input id={answer + i} type="radio" name="answer" value={answer} onChange={this.addSelectedSingle.bind(this, i)}/>
                    <label htmlFor={answer + i}>{answer}</label>
                </div>
        );
      });

      return (
            <div>
                <h1>{text}</h1>
                <div style={{marginTop: "25px"}}>
                    {choices}
                </div>
            </div>
      );
    }

    addSelectedOpenEnded(e) {
      const val = e.target.value;
      this.setState({
        selectedAnswers: [val],
        inputVal: val
      });
    }

    openEndedQuestion(text) {
      return (
            <div>
                <h1>{text}</h1>
                <div style={{marginTop: "25px"}} className="standalone_input_box text_input center_element">
                    <input className="standalone_input_box" type="text" value={this.state.inputVal} onChange={this.addSelectedOpenEnded.bind(this)}/>
                </div>
            </div>
      );
    }

    addSelectedNumber(e) {
      const val = e.target.value;
      const error = !isNaN(parseFloat(val)) && isFinite(val) ? null : "Input must be numeric";

      this.setState({
        selectedAnswers: [val],
        inputVal: val,
        error: error
      });
    }

    numberQuestion(text) {
      return (
        <div>
          <h1>{text}</h1>
          {this.state.error && (<h3>{this.state.error}</h3>)}
          <div style={{marginTop: "25px"}} className="standalone_input_box text_input center_element">
              <input className="standalone_input_box" type="text" value={this.state.inputVal} onChange={this.addSelectedNumber.bind(this)}/>
          </div>
        </div>
      );
    }

    makeDatePicker(element) {
      $(element).datepicker({
        dateFormat: "yy-mm-dd"
      });
    }

    dateQuestion(text) {
      return (
        <div>
          <h1>{text}</h1>
          <div style={{marginTop: "25px"}} className="standalone_input_box text_input center_element">
              <input ref={this.makeDatePicker} value={this.state.inputVal} className="standalone_input_box datepicker" type="text" name="answer" onChange={this.addSelectedOpenEnded.bind(this)}/>
          </div>
        </div>
      );
    }

    getQuestionType() {
      if (this.props.element.input_type === 'ms')
        return this.multipleSelect(this.props.element.text, this.props.element.answers);
      if (this.props.element.input_type === 'ss')
        return this.singleSelect(this.props.element.text, this.props.element.answers);
      if (this.props.element.input_type === 'dt')
        return this.dateQuestion(this.props.element.text);
      if (this.props.element.input_type === 'ot')
        return this.openEndedQuestion(this.props.element.text);
      if (this.props.element.input_type === 'nv')
        return this.numberQuestion(this.props.element.text);
    }

    clickSubmit(e) {
      console.log('submit!');
      // here we need to filter the data and display in the multiselect
      this.props.handleSubmit(this.state.selectedAnswers);
    }

    render() {
      const element = this.getQuestionType();
      return (
            <div>
                {element}
                <Button style={{marginTop: "25px"}} className="center_element" onClick={this.clickSubmit.bind(this)}>
                    Submit
                </Button>
            </div>
      );
    }
  }
  class DashboardFilterMultiSelect extends Component {
    constructor() {
      super();
      this.state = {
        selectedAttribute: {}, // id, input_type, name
        showAttributeModal: false,
        selectedFilters: [],
        selectedQuestion: {}, // {id, name, input_type, position}
        showQuestionModal: false,
        selectFieldOptions: [],
        filterAttributeValue: null
      };
    }
    handleSelectChange(val) {
      this.setState({selectedFilters: val});
    }
    handleSelectAttribute(e) {
      this.setState({
        selectedAttribute: {
          name: e.target.attributes.name.value,
          id: e.target.dataset.id,
          input_type: e.target.dataset.input_type
        },
        showAttributeModal: true
      });
    }
    handleSelectQuestion(question, e) {
      this.setState({
        selectedQuestion: question,
        showQuestionModal: true
      });
    }
    handleChange(e) {
      this.setState({[e.target.attributes.name.value]: e.target.value});
    }
    handleAttributeFilterSubmit(e) {
      e.preventDefault();
      let {selectedFilters, selectedAttribute, filterAttributeValue, selectFieldOptions} = this.state;
      let {name, id} = selectedAttribute;
      let filterDisplay = `${name}=${filterAttributeValue}`;
      this.props.handleFilterSelect(this.props.groupLetter, 'attribute', {id: id, values: filterAttributeValue});
      this.setState({
        selectedFilters: [...selectedFilters, filterDisplay],
        showAttributeModal: false,
        selectFieldOptions: [...selectFieldOptions, {value: filterDisplay, label: filterDisplay}]
      });
    }
    handleQuestionFilterSubmit(answers) {
      let {selectedQuestion, selectFieldOptions, selectedFilters} = this.state;
      let {position, id} = selectedQuestion;
      let filterDisplay = `Question ${position}=${answers.join(',')}`;
      let filterKey = `${position}=${answers.join('.')}`;
      this.props.handleFilterSelect(this.props.groupLetter, 'question', {id: id, values: answers});
      this.setState({
        selectedFilters: [...selectedFilters, filterKey],
        showQuestionModal: false,
        selectFieldOptions: [...selectFieldOptions, {value: filterKey, label: filterDisplay}]
      });
    }
    render() {
      let {showAttributeModal, showQuestionModal, selectedQuestion, selectedAttribute, selectedFilters, selectFieldOptions} = this.state;
      let {questions, attributes, responses, handleSaveGroup, handleCancel} = this.props;
      return (
        <div style={{...thmBackground, ...pam}}>
          <Select
            multi
            simpleValue
            name="filters"
            value={selectedFilters}
            options={selectFieldOptions}
            onChange={this.handleSelectChange.bind(this)}
          />
            <div style={{
              height: 106,
              width: '100%',
              padding: '22px 0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
            <div style={spaceAround}>
              <div className="drop_down" style={boxStyle}>
                Attributes
                <Icon fa="caret-down" style={{
                  marginLeft: 30,
                  marginRight: -10
                }}/>
                <div className="drop_down-content" style={dropDownStyle}>
                  <input type="text" placeholder="search for an attribute"/>
                  {attributes.map(({name, key, id, input_type}) => <li
                    key={key}
                    name={name}
                    data-id={id}
                    data-input_type={input_type}
                    onClick={this.handleSelectAttribute.bind(this)}>
                    {name}
                   </li>)}
                </div>
              </div>
              <div className="drop_down" style={boxStyle}>
                Question Responses
                <Icon fa="caret-down" style={{
                  marginLeft: 30,
                  marginRight: -10
                }}/>
                <div className="drop_down-content" style={dropDownStyle}>
                  {questions.map((question, i) => <li
                    key={question.key}
                    onClick={this.handleSelectQuestion.bind(this, question)}>
                    {question.position}. {question.name}
                   </li>)}
                </div>
              </div>
              </div>
              <div>
                <Button onClick={handleSaveGroup} style={mas}>Save Group</Button>
                <Button onClick={handleCancel} style={mas}>Cancel</Button>
              </div>
            </div>

            {showAttributeModal ?
              <ModalDialog
              onDismiss={_ => this.setState({showAttributeModal: false})}
              style={{width: 674, padding: '50px 0'}}
            >
              <div style={[flexCenter, {flexDirection: 'column'}]}>
                <h1 style={{
                  color: 'black',
                  fontSize: '20px'
                }}>
                  Filter participants whose {selectedAttribute.name.toLowerCase()} is...
                </h1>
                <h2 style={{
                  fontWeight: 'normal',
                  fontSize: '15px'
                }}>
                </h2>
                <div style={{
                  width: '90%',
                  maxHeight: 378,
                  overflow: 'auto',
                  border: freeResponseBorder,
                  borderRadius: 7
                }}>
                <form action="#" onSubmit={this.handleAttributeFilterSubmit.bind(this)}>
                  <input name="filterAttributeValue" type="text" placeholder={`Enter ${selectedAttribute.name.toLowerCase()}`} style={{width: '100%'}} onChange={this.handleChange.bind(this)}/>
                  <button>Submit</button>
                </form>
              </div>
            </div>
            </ModalDialog> : null}
            {showQuestionModal ?
              <ModalDialog
              onDismiss={_ => this.setState({showQuestionModal: false})}
              style={{width: 674, padding: '50px 0'}}
            >
              <div style={[flexCenter, {flexDirection: 'column'}]}>
                <h1 style={{
                  color: 'black',
                  fontSize: '20px'
                }}>
                  Filter participants who answered the following for
                  question {selectedQuestion.position}. {selectedQuestion.name} ?
                </h1>
                <h2 style={{
                  fontWeight: 'normal',
                  fontSize: '15px'
                }}>
                </h2>
                <QuestionViewFilter
                  element={selectedQuestion.phase_element}
                  handleSubmit={this.handleQuestionFilterSubmit.bind(this)}
                />
            </div>
            </ModalDialog> : null}
          </div>
      );
    }
  }

  const PieChart = props => {
    const options = {
      legend: {
        labels: {
          boxWidth: 10,
          fontColor: '#454B56',
          usePointStyle: true
        }
      },
      tooltips: {
        callbacks: {
          // We pad labels with spaces as an alignment hack.
          // The spaces shouldn't show up in tooltips, so trim them here.
          label: (item, data) => {
            const label = data.labels[item.index].trim();
            const n = data.datasets[item.datasetIndex].data[item.index];
            return `${label}: ${n}`;
          }
        }
      },
      title: {display: false}
    };
    return <ReactChart type="pie" {...props} options={options}/>;
  };

  const BarChart = props => {
    const options = {
      legend: {display: false},
      scales: {
        xAxes: [{
          display: false,
          ticks: {
            beginAtZero: true
          }
        }],
        yAxes: [{
          barThickness: 7,
          gridLines: {
            drawBorder: false,
            display: false
          },
          ticks: {
            fontColor: 'black'
          }
        }]
      },
      title: {display: false}
    };
    return <ReactChart type="horizontalBar" {...props} options={options}/>;
  };

  const VerticalBarChart = props => {
    const options = {
      legend: {
        display: true
      },
      scales: {
        xAxes: [{
          display: true,
          barThickness: 16,
          ticks: {
            beginAtZero: true
          }
        }],
        yAxes: [{
          gridLines: {
            drawBorder: false,
            display: false
          },
          ticks: {
            fontColor: 'black'
          }
        }]
      },
      title: {display: false}
    };
    return <ReactChart type="bar" {...props} options={options}/>;
  };

  const sorted = arr => {
    arr.sort();
    return arr;
  };

  // ResponseBreakdown implements the views of both user attributes and question
  // responses. The two views are similar enough to share an implementation.
  @Radium
  class ResponseBreakdown extends Component {
    constructor(props) {
      super(props);
      this.state = {responseModal: null};
    }

    render() {
      const {data, label, questions, isQuestions} = this.props;

      // We need to massage the structure of `data` a bit to make it
      // easier to use here.
      //
      // current data structure: [
      //    {
      //      id,  // question id,
      //      value, // a single user's value for this question
      //      user_id // id of user who gave this answer
      //    } // one per answer of any question
      //  ]

      const groupByKey = (arr, keyField, groupField) => {
        return arr
          .sort(
              (a, b) => String(a[keyField]).localeCompare(String(b[keyField]))
          ).reduce((arr, v, i) => {
            const key = v[keyField];
            if (i === 0 || arr.slice(-1)[0][keyField] !== key) {
              arr.push({[keyField]: key, [groupField]: []});
            }
            arr.slice(-1)[0][groupField].push(v);
            return arr;
          }, []);
      };

      const chartData = groupByKey(data, 'id', 'questions')
        .map(({id, questions}) => ({
          id: id,
          values: groupByKey(questions, 'value', 'answers')
            .map(({value, answers}) => ({value, n: answers.length}))
        }));

      // new data structure: [
      //    {
      //      id, // question id
      //      values: [
      //        value, // An answer
      //        n // Number of users who gave it.
      //      ]
      //    } // one per question
      // ]

      const borderTop = {borderTop: border};
      let currentResponse = null;
      let currentQuestion = null;
      const {responseModal} = this.state;
      if (responseModal !== null) {
        currentResponse = chartData[this.state.responseModal];
        currentQuestion = questions.find(({id}) => id === currentResponse.id);
      }
      return <div style={{width: '47%'}}>
        {currentResponse !== null && (
          <ModalDialog
            onDismiss={_ => this.setState({responseModal: null})}
            style={{width: 674, padding: '50px 0'}}
          >
            <div style={[flexCenter, {flexDirection: 'column'}]}>
              <h1 style={{
                color: 'black',
                fontSize: '20px'
              }}>
                Question Responses
              </h1>
              <h2 style={{
                fontWeight: 'normal',
                fontSize: '15px'
              }}>
                {`Question ${responseModal + 1}: ${currentQuestion.name}`}
              </h2>
              <div style={{
                width: '90%',
                maxHeight: 378,
                overflow: 'auto',
                border: freeResponseBorder,
                borderRadius: 7
              }}>{
                data
                  .filter(({id}) => id === currentQuestion.id)
                  .map(({user_id, value}, i) => (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        width: '100%',
                        borderTop: i === 0 ? 'none' : freeResponseBorder
                      }}
                    >
                      <div style={{width: '25%'}}>
                        <div style={{
                          backgroundColor: '#66D9CC',
                          borderRadius: '100px',
                          color: 'white',
                          padding: 5,
                          margin: 10,
                          textTransform: 'uppercase',
                          fontSize: 'smaller'
                        }}>
                          {`Participant ${user_id}`}
                        </div>
                      </div>
                      <div style={{
                        margin: 10,
                        width: '75%',
                        textAlign: 'left',
                        color: 'darkgrey'
                      }}>
                        {value}
                      </div>
                    </div>
                  ))
              }</div>
            </div>
          </ModalDialog>
        )}
        <h1 style={{color: 'black', fontSize: '26px'}}>{label}</h1>
        <div className="force_scroll" style={{
          border: border,
          borderRadius: '7px',
          overflowY: 'scroll',
          overflowX: 'hidden',
          maxHeight: 300,
          width: '100%'
        }}>{
          chartData.map((q, i) => {
            const question = questions.find(({id}) => id === q.id);
            const maxLabelWidth = 25;
            const spaces = ' '.repeat(maxLabelWidth);
            let height;
            switch (question.input_type) {
              case 'ss':
                height = 160;
                break;
              case 'ms':
                height = 138;
                break;
              default:
                height = 102;
                break;
            }
            let padding;
            if (isQuestions) {
              padding = '0 44px 0 56px';
            } else {
              padding = '0 44px 0 20px';
            }
            return <div
              key={q.id}
              style={{
                height,
                width: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                position: 'relative',
                borderTop: i === 0 ? 'none' : border,
                padding
              }}
            >
              <div/>
              {isQuestions &&
                <span style={{
                  position: 'absolute',
                  top: 24,
                  left: 22,
                  display: 'inline-block',
                  width: 21,
                  height: 21,
                  paddingTop: '1px',
                  lineHeight: '21px',
                  color: 'white',
                  backgroundColor: '#454B56',
                  borderRadius: 50,
                  textAlign: 'center'
                }}>
                  {`${i + 1}`}
                </span>
              }
              <h3 style={{
                margin: 0,
                color: '#BABBC0',
                fontWeight: 'lighter',
                fontSize: 16
              }}>
                {question.name}
              </h3>
              {(_ => {
                switch (question.input_type) {
                  case 'ms':
                    return (
                      <div style={{
                        width: '90%',
                        height: '60%'
                      }}>
                        <BarChart
                          data={{
                            labels: q.values.map(v => v.value),
                            datasets: [{
                              data: q.values.map(v => v.n),
                              backgroundColor: '#F6CDDE'
                            }]
                          }}
                        />
                      </div>
                    );
                  case 'ss':
                    return (
                      <div style={{
                        width: '90%',
                        height: '60%'
                      }}>
                        <PieChart
                          data={{
                            labels: q.values.map(v => {
                              const overflow = v.value.length - maxLabelWidth;
                              return '  ' + (overflow > 0 ?
                                v.value.slice(0, maxLabelWidth - 3) + '...' :
                                v.value + spaces.slice(0, -overflow));
                            }),
                            datasets: [{
                              data: q.values.map(v => v.n),
                              backgroundColor: [
                                '#EB5092',
                                '#82CEC9',
                                '#F6B3D0',
                                '#B2E0E1'
                              ],
                              borderWidth: q.values.map(_ => 0)
                            }]
                          }}
                        />
                      </div>
                    );
                  default:
                    return (
                      <Button clear onClick={_ => this.setState({
                        responseModal: i
                      })}>
                        View Responses
                      </Button>
                    );
                }
              })()}
              <div/>
            </div>;
          })
        }</div>
      </div>;
    }
  }

  // NumberScroll is a component that lets you type a number or click "up" or
  // "down" buttons to increment or decrement it. You can also hold down
  // on the buttons to increment/decrement faster.
  @Radium
  class NumberScroll extends Component {
    constructor(props) {
      super(props);
      this.clearInterval = this.clearInterval.bind(this);
      this.clickUp = this.clickUp.bind(this);
      this.clickDown = this.clickDown.bind(this);
      this.interval = null;
      this.input = null;
      this.state = {focused: false, input: ''};
    }

    blur() {
      if (this.input) {
        this.input.blur();
      }
    }

    focus() {
      if (this.input) {
        this.input.focus();
      }
    }

    clickUp() {
      const {n, min, max, onChange} = this.props;
      if (n < max) {
        onChange(n + 1);
      } else {
        onChange(min);
      }
    }

    clickDown() {
      const {n, min, max, onChange} = this.props;
      if (n > min) {
        onChange(n - 1);
      } else {
        onChange(max);
      }
    }

    componentWillUnmount() {
      this.clearInterval();
    }

    clearInterval() {
      if (this.interval) {
        clearInterval(this.interval);
      }
      if (this.timeout) {
        clearTimeout(this.timeout);
      }
    }

    setIntervalAfter(fn, delay, wait) {
      clearInterval();
      const self = this;
      this.timeout = setTimeout(_ => {
        self.timeout = null;
        self.interval = setInterval(fn, delay);
      }, wait);
    }

    render() {
      const {n, min, max, numWidth, charWidth, height, fontSize} = this.props;
      const width = charWidth * numWidth;
      const repeatDelay = 70;
      const mouseHoldDelay = 600;
      const arrowStyle = {
        'cursor': 'pointer',
        ':hover': {
          color: '#3498DB'
        }
      };
      const {focused, input} = this.state;
      const zeros = x => new Array(x).fill("0").join('');
      // Based on http://stackoverflow.com/a/14760377/3072514
      const nString = String(zeros(numWidth) + n).slice(-numWidth);
      return <div style={{
        width,
        height,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontWeight: 900
      }}>
        <Icon
          fa="angle-up fa-2x"
          onClick={this.clickUp}
          onMouseDown={_ => this.setIntervalAfter(
              this.clickUp, repeatDelay, mouseHoldDelay
          )}
          onMouseUp={this.clearInterval}
          onMouseOut={this.clearInterval}
          style={arrowStyle}
        />
        <input
          type="text"
          style={{
            width,
            fontSize,
            textAlign: 'center',
            height: fontSize,
            paddingTop: 8
          }}
          min={min}
          max={max}
          maxLength={numWidth}
          placeholder={nString}
          inputMode="numeric"
          value={focused ? input : nString}
          ref={input => {
            this.input = input;
          }}
          onFocus={_ => this.setState({focused: true})}
          onBlur={_ => {
            const x = parseInt(input, 10);
            if (input && min <= x && x <= max) {
              this.props.onChange(parseInt(input, 10));
            }
            this.setState({focused: false, input: ''});
          }}
          onChange={e => {
            const text = e.target.value;
            if (/^[0-9]*$/.test(text) && text.length <= numWidth) {
              this.setState({input: text}, _ => {
                if (text.length === numWidth) {
                  setTimeout(this.props.onComplete());
                }
              });
            }
          }}
          onKeyDown={e => {
            if (e.keyCode === 8 && input === '') {
              this.props.onGoBack();
            }
          }}
        />
        <Icon
          fa="angle-down fa-2x"
          onClick={this.clickDown}
          onMouseDown={_ => this.setIntervalAfter(
              this.clickDown, repeatDelay, mouseHoldDelay
          )}
          onMouseUp={this.clearInterval}
          onMouseOut={this.clearInterval}
          style={arrowStyle}
        />
      </div>;
    }
  }
  NumberScroll.defaultProps = {max: 59, min: 0};

  // TimeInput is a custom time input component.
  class TimeInput extends Component {
    constructor(props) {
      super(props);
      this.inputs = [];
    }

    render() {
      const fontSize = 40;
      const duration = moment.duration(this.props.value, 'milliseconds');
      const nsProps = i => ({
        charWidth: 25,
        height: 103,
        numWidth: 2,
        fontSize: fontSize,
        ref: input => {
          this.inputs[i] = input;
        },
        onComplete: _ => {
          if (this.inputs[i]) {
            this.inputs[i].blur();
          }
          if (this.inputs[i + 1]) {
            this.inputs[i + 1].focus();
          }
        },
        onGoBack: _ => {
          if (this.inputs[i]) {
            this.inputs[i].blur();
          }
          if (this.inputs[i - 1]) {
            this.inputs[i - 1].focus();
          }
        }
      });
      const unitProps = (unit, i) => (Object.assign(nsProps(i), {
        n: duration[unit](),
        onChange: n => {
          this.props.onChange(
              moment.duration(duration)
                .subtract(duration[unit](), unit)
                .add(n, unit)
                .asMilliseconds()
              );
        }
      }));
      return <div style={{
        min: 0,
        max: 59,
        width: 295,
        height: 103,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <Style rules={{span: {color: 'black'}}}/>
        <NumberScroll {...unitProps("hours", 0)}/>
        <span style={{fontSize}}>:</span>
        <NumberScroll {...unitProps("minutes", 1)}/>
        <span style={{fontSize}}>:</span>
        <NumberScroll {...unitProps("seconds", 2)}/>
        <span style={{fontSize}}>.</span>
        <NumberScroll
          {...nsProps(3)}
          max={9}
          numWidth={1}
          n={duration.milliseconds() / 100}
          onChange={n => {
            // This assumes that the duration is always
            // a multiple of 100ms. So does `n`, above.
            this.props.onChange(
                moment.duration(duration)
                  .subtract(duration.milliseconds(), 'milliseconds')
                  .add(n * 100, 'milliseconds')
                  .asMilliseconds()
            );
          }}
        />
      </div>;
    }
  }

  // Space is a shorthand way to add space to a view.
  // It is more convenient to use than margins and padding in some cases.
  const Space = ({height, width}) => <div style={{height, width}}/>;

  // MarkEventModal implements the UI for adding event markers.
  @Radium
  class MarkEventModal extends Component {
    constructor(props) {
      super(props);

      this.state = {
        description: '',
        timestamp1: null,
        timestamp2: null,
        screen: 'select-type',
        showErrors: false
      };

      this.headerStyle = {
        color: 'black',
        fontWeight: 'bold',
        fontSize: 22
      };

      this.buttonStyle = {
        textTransform: 'uppercase',
        width: 130
      };

      this.shadowOutline = {
        border: border,
        borderRadius: 7,
        boxShadow: '0 0 2px rgba(0,0,0,0.2)'
      };
    }

    renderCancelButton() {
      return <Button
        clear={true}
        onClick={this.props.onClose}
        buttonStyle={this.buttonStyle}
      >
        Cancel
      </Button>;
    }

    // renderSelectType is the first screen of the event marking flow
    renderSelectType() {
      const eventButton = {
        width: '100%',
        height: '70px',
        display: 'flex',
        justifyContent: 'space-between',
        paddingLeft: 36,
        paddingRight: 24,
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        fontSize: 16
      };
      return <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <h1 style={[this.headerStyle, {width: 280}]}>
          What type of event would you like to add?
        </h1>
        <Space height={38}/>
        <div style={[this.shadowOutline, {width: '100%'}]}>
          <button
            style={[eventButton, {borderBottom: border}]}
            onClick={_ => this.setState({screen: 'single', showErrors: false})}
          >
            Single time point event
            <Icon fa="caret-right"/>
          </button>
          <button
            style={eventButton}
            onClick={_ => this.setState({screen: 'multi', showErrors: false})}
          >
            Multi time point event
            <Icon fa="caret-right"/>
          </button>
        </div>
        <Space height={30}/>
        {this.renderCancelButton()}
      </div>;
    }

    // renderInput is the second screen of the event marking flow
    renderInput(single) {
      const headerHeight = 52;
      let errors = [];
      const t1 = this.state.timestamp1;
      const t2 = this.state.timestamp2;
      const maxMS = this.props.maxTime * 1000;

      // Input validation.
      // We just identify errors here. Rendering decisions are made below.
      if (single) {
        if (t1 === 0 || t1 === null) {
          errors.push('Timestamp should not be zero');
        }
        if (t1 > maxMS) {
          errors.push('This timestamp is outside the length of the media.');
        }
      }
      if (!single) {
        if (t2 === 0 || t2 === null) {
          errors.push('End time should not be zero.');
        } else if (t2 === t1) {
          errors.push('Start time and end time should be different.');
        } else if (t2 < t1) {
          errors.push('End time should be after start time.');
        }
        if (t1 > maxMS && t2 > maxMS) {
          errors.push('Both timestamps are outside the length of the media.');
        } else if (t2 > maxMS) {
          errors.push('End time is outside the length of the media.');
        }
        if (t2 % 500 != 0) {
          errors.push('Last digit must be 5 or 0');
        }
      }
      if (t1 % 500 != 0) {
        errors.push('Last digit must be 5 or 0');
      }

      // Render.
      return <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        {this.state.showErrors &&
          <ul className="flashes">
            {errors.map((err, i) =>
              <div key={i} className="center_element center alert alert-danger">
                <li className="error">{err}</li>
              </div>
            )}
          </ul>
        }
        <div style={[flexCenter, {
          width: '100%',
          height: headerHeight,
          position: 'relative'}]}
        >

          {/* Back button */}
          <Icon
            fa="caret-left"
            onClick={_ => this.setState({screen: 'select-type'})}
            style={[this.shadowOutline, flexCenter, {
              position: 'absolute',
              left: 0,
              width: headerHeight,
              height: headerHeight,
              cursor: 'pointer'
            }]}/>

          <h1 style={this.headerStyle}>
            {(single ? 'Single' : 'Multiple') + ' point time event'}
          </h1>

        </div>
        <span>
          The maximum resolution is half a second.
        </span>
        <TimeInput
          value={this.state.timestamp1}
          onChange={n => this.setState({timestamp1: n})}/>
        {single || <TimeInput
          value={this.state.timestamp2}
          onChange={n => this.setState({timestamp2: n})}/>
        }
        <Space height={37}/>
        Enter event details:
        <Space height={22}/>
        <textarea
          value={this.state.description}
          onChange={e => this.setState({description: e.target.value})}
          style={[this.shadowOutline, {
            width: '100%',
            height: 180,
            padding: 20
          }]}/>
        <Space height={29}/>
        <div style={{
          display: 'flex',
          justifyContent: 'center'
        }}>
          {this.renderCancelButton()}
          <Space width={7}/>
          <div style={{width: 7}}/>
          <Button
            onClick={_ => {
              if (errors.length) {
                this.setState({showErrors: true});
                return;
              }
              const {description, timestamp1, timestamp2} = this.state;
              this.props.onSave({description, timestamp1, timestamp2});
              this.props.onClose();
            }}
            buttonStyle={this.buttonStyle}>
            Save
          </Button>
        </div>
      </div>;
    }

    renderSingle() {
      return this.renderInput(true);
    }

    renderMulti() {
      return this.renderInput(false);
    }

    render() {
      const {onClose} = this.props;
      // We have several different screens. Determine which screen to use
      // and then delegate to the appropriate renderer.
      let which;
      switch (this.state.screen) {
        case 'select-type':
          which = this.renderSelectType;
          break;
        case 'single':
          which = this.renderSingle;
          break;
        case 'multi':
          which = this.renderMulti;
          break;
        default:
          console.log('No such screen: ' + this.state.screen);
          which = _ => null;
      }
      return <div className="dialog_modal">
        <div className="dialog_modal_box" style={{
          width: 517,
          height: 'unset',
          padding: '50px 40px 40px 40px'
        }}>
          {which.bind(this)()}
        </div>
      </div>;
    }
  }

  // Header implements the emotion graph controls and media player.
  @Radium
  class Header extends Component {
    constructor(props) {
      super(props);
      this.state = {
        showEventModal: false,
        showDashboardFilter: false,
        selectedGroup: null,
        heatmapLoaded: false
      };
    }
    componentDidMount() {
      // create configuration object for heatmap
      // must load AFTER image or video has loaded so that we get the right size
      // this hack shouldn't matter because the default is to not show heat data until
      // the eye is clicked
      setTimeout(() => {
        let heatmapContainer = document.getElementById('heatmapContainer');
        let config = {
          container: heatmapContainer,
          radius: 30,
          maxOpacity: .5,
          minOpacity: 0.01,
          blur: .75
        };
        // create heatmap with configuration
        this.heatmapInstance = h337.create(config);
        this.setState({heatmapLoaded: true});
      }, 1500);
    }
    componentWillUpdate(nextProps, nextState) {
      if (this.heatmapInstance && (this.state.showHeatMap && !nextState.showHeatMap)) {
        this.heatmapInstance.setData({
          max: 0,
          min: 0,
          data: []
        });
      }
    }
    handleAddGroupClick(letter) {
      this.setState({
        showDashboardFilter: true,
        selectedGroup: letter
      });
    }
    handleSaveGroup() {
      this.props.addGroup(this.state.selectedGroup);
      this.setState({
        showDashboardFilter: false,
        selectedGroup: null
      });
    }
    handleCancel() {
      this.setState({
        showDashboardFilter: false,
        selectedGroup: null
      });
    }
    handleEyeClick() {
      this.setState({showHeatMap: !this.state.showHeatMap});
    }
    render() {
      const {experimentName, media, mediaSelected, onMediaUpdate, addGroup, groups, questions, attributes, responses, handleFilterSelect, groupA, groupB} = this.props;
      const {selectedGroup} = this.state;
      const currentMedia = media.find(m => m.key === mediaSelected);
      return <div style={{display: 'flex'}}>
        <div style={{width: '70%', position: 'relative'}}>
          <h1 style={{color: '#ddd', fontWeight: 'bold', margin: '31px 0'}}>
            {experimentName}
          </h1>
          <Icon fa="eye" style={[iconStyle, this.state.showHeatMap ? null : disabled, clickable, {
            position: 'absolute',
            top: 0,
            right: 0
          }]} onClick={this.handleEyeClick.bind(this)}/>
          <hr style={{marginBottom: 0}}/>
            {this.state.showDashboardFilter ?
              <DashboardFilterMultiSelect
                questions={questions}
                attributes={attributes}
                responses={responses}
                handleFilterSelect={handleFilterSelect}
                groupLetter={selectedGroup}
                handleSaveGroup={this.handleSaveGroup.bind(this)}
                handleCancel={this.handleCancel.bind(this)}
              /> :
              <div style={{
                height: 106,
                width: '100%',
                padding: '22px 0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>

              {groupA.exists ?
                <div style={[boxStyle]}>Group A</div>
                : <div style={[boxStyle, clickable]} onClick={this.handleAddGroupClick.bind(this, 'A')}>Add Group A</div>
              }
              {groupB.exists ?
                <div style={[boxStyle]}>Group B</div>
                : <div style={[boxStyle, clickable]} onClick={this.handleAddGroupClick.bind(this, 'B')}>Add Group B</div>
              }
                <div className="drop_down" style={boxStyle}>
                  {currentMedia.name}
                  <Icon fa="caret-down" style={{
                    marginLeft: 30,
                    marginRight: -10
                  }}/>
                  <div className="drop_down-content" style={dropDownStyle}>
                    {media.map(({name, key}) => <li
                      key={key}
                      onClick={_ => onMediaUpdate({name, key})}>
                      {name}
                     </li>)}
                  </div>
                </div>
                <div
                  style={[boxStyle, {cursor: 'pointer'}]}
                  onClick={_ => this.setState({showEventModal: true})}
                >
                  Mark event
                </div>
              </div>
            }
        </div>
        <Space width="2%"/>
        <div style={[flexCenter, {width: '28%'}]}>
          {(() => {
            const props = {
              src: currentMedia.file_name,
              ref: ref => {
                if (ref) {
                  ['timeupdate', 'loadedmetadata'].forEach(event => {
                    ref.addEventListener(event, () => {
                      mediaPosition = ref.currentTime / ref.duration;
                      currentTime = ref.currentTime;
                      let newKey = currentTime.toFixed(0);
                      if (this.state.heatmapLoaded && this.state.showHeatMap) {
                        let {gaze_data} = currentMedia;
                        let newDataSet = gaze_data.data[newKey];
                        if (newDataSet && !_.isEmpty(newDataSet)) {
                          let data = {
                            max: gaze_data.max,
                            min: gaze_data.min,
                            data: newDataSet
                          };
                          this.heatmapInstance.setData(data);
                        }
                      }
                      updatePlayahead();
                    });
                  });
                }
              },
              style: {
                maxWidth: '100%',
                maxHeight: '100%'
              }
            };
            switch (currentMedia.content_type) {
              case 'i':
                return (
                  <div>
                    <div id="heatmapContainer"><img {...props} /></div>
                    <audio {...props} src={'../static/mp3/' + Math.floor(currentMedia.duration_ms / 1000) + '_seconds.mp3'} controls></audio>
                  </div>
                );
              case 'v':
                return <video {...props} id="heatmapContainer" controls/>;
              case 'a':
                return <audio {...props} controls/>;
              default:
                return null;
            }
          })()}
        </div>
        {this.state.showEventModal &&
          <MarkEventModal
            onClose={_ => this.setState({showEventModal: false})}
            onSave={this.props.onEventMarkerAdded}
            maxTime={this.props.mediaLength}
          />
        }
      </div>;
    }
  }

  // Dashboard is the top-level component for this page.
  class Dashboard extends Component {
    constructor() {
      super();
      this.state = {
        groupA: {
          exists: false,
          questionFilters: [],
          attributeFilters: []
        },
        groupB: {
          exists: false,
          questionFilters: [],
          attributeFilters: []
        },
        showModal: false,
        currentMedia: null
      };
    }
    componentWillMount() {
      this.setState({currentMedia: this.props.media[0]});
    }
    addGroup(groupLetter) {
      let groupLabel = 'group' + groupLetter;
      let newGroupData = this.state[groupLabel];
      newGroupData.exists = true;
      this.setState([groupLabel]: newGroupData);
    }

    removeGroup(groupLetter) {
      let groupLabel = 'group' + groupLetter;
      let newGroupData = this.state[groupLabel];
      newGroupData.exists = false;
      this.setState({
        [groupLabel]: newGroupData
      });
    }

    handleFilterSelect(groupLetter, type, filter) {
      let groupLabel = 'group' + groupLetter;
      let newGroupData = this.state[groupLabel];
      newGroupData[type + 'Filters'] = [...this.state[groupLabel][type + 'Filters'], filter];
      this.setState({
        [groupLabel]: newGroupData
      });
    }
    // filters have id and values
    // id - question: question id, attribute:
    // compose filters for attributes and responses
    applyFilters(filters, data) {
      filters.forEach(filter => {
        let {id, values} = filter;
        data = data.filter(item => item.id === id)
          .filter(item => _.includes(values, item.value || item.name));
      });
      return data;
    }
    showModal() {
      this.setState({showModal: true});
    }
    _attachData(group, responses, user_attributes, currentMedia) {
      if (group.exists) {
        let responsesB = this.applyFilters(group.questionFilters, responses);
        let user_attributesB = this.applyFilters(group.attributeFilters, user_attributes);
        // filter out responses and user attributes based on the intersection of user_ids
        let user_ids = _.intersection(responsesB.map(response => response.user_id), user_attributesB.map(user_attr => user_attr.user_id));
        group.responses = responsesB.filter(res => _.includes(user_ids, res.user_id));
        group.user_attributes = user_attributesB.filter(res => _.includes(user_ids, res.user_id));
        // group.currentMediaData = currentMedia.data.filter(res => _.includes(user_ids, res.user_id));
      }
    }
    downloadAsCSV() {
      downloadCSV({filename: "emotiv-data.csv"}, this.state.currentMedia.data);
    }
    downloadAsJSON() {
      let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.props.users));
      let dlAnchorElem = document.getElementById('downloadAnchorElem');
      dlAnchorElem.setAttribute("href", dataStr);
      dlAnchorElem.setAttribute("download", "emotiv-user-data.json");
      dlAnchorElem.click();
    }
    setMediaForDownload(media) {
      this.setState({currentMedia: media});
    }
    updateMediaForDownload(data) {
      let newMedia = this.state.currentMedia;
      newMedia.data = data;
      this.setState({currentMedia: newMedia});
    }

    render() {
      const {experimentName, users, attributes, questions, media} = this.props;
      const {groupA, groupB, showModal} = this.state;
      const user_attributes = users.reduce(
          (all, {attributes}) => all.concat(attributes),
          []);
      const responses = users.reduce(
          (all, {responses}) => all.concat(responses),
          []);
      this._attachData(groupA, responses, user_attributes);
      this._attachData(groupB, responses, user_attributes);
      return (
        <div style={{marginBottom: 100}}>
          <EmotionGraphContainer
            experimentName={experimentName}
            media={media}
            questions={questions}
            attributes={attributes}
            responses={responses}
            handleFilterSelect={this.handleFilterSelect.bind(this)}
            groupA={groupA}
            groupB={groupB}
            addGroup={this.addGroup.bind(this)}
            removeGroup={this.removeGroup.bind(this)}
            setMediaForDownload={this.setMediaForDownload.bind(this)}
            updateMediaForDownload={this.updateMediaForDownload.bind(this)}
          />
          <div style={{
            display: 'flex',
            justifyContent: 'flex-end',
            width: '100%'
          }}>
            <Button
              style={{margin: '21px 0'}}
              onClick={this.showModal.bind(this)}
              clear={true}>
              Download All Recordings
            </Button>
          </div>
          {!groupA.exists && !groupB.exists ?
            <div style={spaceBetween}>
              <ResponseBreakdown
                label="User Attributes"
                questions={attributes}
                data={user_attributes}/>
              <ResponseBreakdown
                label="Question Responses"
                questions={questions}
                isQuestions
                data={responses}/>
            </div> : null }
          {groupA.exists ?
            <div style={spaceBetween}>
              <h3>Group A</h3>
              <ResponseBreakdown
                label="User Attributes"
                questions={attributes}
                data={groupA.user_attributes}/>
              <ResponseBreakdown
                label="Question Responses"
                questions={questions}
                isQuestions
                data={groupA.responses}/>
            </div> : null }
          {groupB.exists ?
            <div style={spaceBetween}>
              <h3>Group B</h3>
              <ResponseBreakdown
                label="User Attributes"
                questions={attributes}
                data={groupB.user_attributes}/>
              <ResponseBreakdown
                label="Question Responses"
                questions={questions}
                isQuestions
                data={groupB.responses}/>
            </div> : null}
            {showModal ?
              <ModalDialog
                onDismiss={_ => this.setState({showModal: false})}
                style={{width: 674, padding: '50px 0'}}
              >
                <h1 style={{
                  color: 'black',
                  fontSize: '20px',
                  marginBottom: '40px'
                }}>
                  Choose Your File Type
                </h1>
                <div style={spaceAround}>
                  <Button onClick={this.downloadAsJSON.bind(this)}> Download user data </Button>
                  <Button onClick={this.downloadAsCSV.bind(this)}> Download headset data </Button>
                </div>
              </ModalDialog>
          : null}
          <a id="downloadAnchorElem" style={{display: 'none'}}></a>
      </div>
      );
    }
  }

  // HELPER FUNCTIONS
  function convertArrayOfObjectsToCSV(args) {
    let result, ctr, keys, columnDelimiter, lineDelimiter, data;

    data = args.data || null;
    if (data === null || !data.length) {
      return null;
    }

    columnDelimiter = args.columnDelimiter || ',';
    lineDelimiter = args.lineDelimiter || '\n';

    keys = Object.keys(data[0]);

    result = '';
    result += keys.join(columnDelimiter);
    result += lineDelimiter;

    data.forEach(function(item) {
      ctr = 0;
      keys.forEach(function(key) {
        if (ctr > 0) result += columnDelimiter;

        result += item[key];
        ctr++;
      });
      result += lineDelimiter;
    });

    return result;
  }

  function downloadCSV(args, inputData) {
    let data, filename, link;
    let csv = convertArrayOfObjectsToCSV({
      data: inputData
    });
    if (csv === null) return;

    filename = args.filename || 'export.csv';

    if (!csv.match(/^data:text\/csv/i)) {
      csv = 'data:text/csv;charset=utf-8,' + csv;
    }
    data = encodeURI(csv);

    link = document.createElement('a');
    link.setAttribute('href', data);
    link.setAttribute('download', filename);
    link.click();
  }

  ReactDOM.render(
    <Dashboard {...dashboardProps} />,
    document.getElementById("dashboard")
  );
});
