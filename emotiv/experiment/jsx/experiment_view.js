requirejs([
  'bluebird',
  'es6-polyfill',
  'whatwg-fetch',
  'moment',
  'react',
  'reactDOM',
  _es6('components'),
], (a, b, c, moment, React, ReactDOM, Components) => {
  const {Component} = React;
  const {Button} = Components;

  class ImageElement extends Component {
    componentDidMount() {
        const startTimeStampString = new Date().toISOString();

        const intervalId = setInterval(() => {
            const endTimestampString = new Date().toISOString();
            clearInterval(intervalId);

            this.props.updateDuration(this.props.element.id, startTimeStampString, endTimestampString);
            this.props.getNextElement(null);
        }, this.props.element.duration_ms);
    }

    render() {
        return (
            <div>
                <h1>Please look at the following image</h1>
                <img width="500px" src={this.props.element.file_name}/>
            </div>
        )
    }
  }

  class VideoElement extends Component {
    componentDidMount() {
        let video = document.getElementById("phaseVideo");
        video.addEventListener('loadedmetadata', () => {
            const startTimeStampString = new Date().toISOString();

            const intervalId = setInterval(() => {
                const endTimestampString = new Date().toISOString();
                clearInterval(intervalId);

                this.props.updateDuration(this.props.element.id, startTimeStampString, endTimestampString);
                this.props.getNextElement(null);
            }, video.duration * 1000);
        });
    }

    render() {
        return (
            <div>
                <h1>Please watch the following video</h1>
                <video src={this.props.element.file_name} id="phaseVideo" width="500" height="500" autoPlay>
                </video>
            </div>
        )
    }
  }
  
  class AudioElement extends Component {
    componentDidMount() {
        let audio = document.getElementById("phaseAudio");
        audio.addEventListener('loadedmetadata', () => {
            const startTimeStampString = new Date().toISOString();

            const intervalId = setInterval(() => {
                const endTimestampString = new Date().toISOString();
                clearInterval(intervalId);

                this.props.updateDuration(this.props.element.id, startTimeStampString, endTimestampString);
                this.props.getNextElement(null);
            }, audio.duration * 1000);
        });
    }

    render() {
        return (
            <div>
                <h1>Please listen to the following recording</h1>
                <audio src={this.props.element.file_name} id="phaseAudio" autoPlay>
                </audio>
            </div>
        )
    }
    
  }


  class TextView extends Component {
    render() {
        return (
            <div>
                <h2 className="shaded-color">{this.props.element.text}</h2>
                <Button className="center_element" onClick={this.props.getNextElement}>
                    Submit
                </Button>
            </div>
        )
    }
  }

  class QuestionView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            selected: {},
            selectedAnswers: [],
            inputVal: ""
        }
    }

    addSelectedMultiple(i) {
        let selected = this.state.selected;
        selected[i] = !selected[i];
        const selectedAnswers = Object.keys(this.state.selected).map((x) => { return this.props.element.answers[x] });
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
            )
        });

        return (
            <div>
                <h1>{text}</h1>
                <h3>Choose all that apply</h3>
                <div style={{marginTop: "25px"}}>
                    {choices}
                </div>
            </div>
        )
    }

    addSelectedSingle(i) {
        const selected = {};
        selected[i] = true;
        const selectedAnswers = Object.keys(selected).map((x) => { return this.props.element.answers[x] });
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
            )
        });
 
        return (
            <div>
                <h1>{text}</h1>
                <div style={{marginTop: "25px"}}>
                    {choices}
                </div>
            </div>
        )
    }

    addSelectedOpenEnded(e) {
        const val = e.target.value;
        this.setState({
            selectedAnswers: [val],
            inputVal: val,
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
        )
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
        )
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
        )
    }

    getQuestionType() {
        if (this.props.element.input_type == 'ms')
            return this.multipleSelect(this.props.element.text, this.props.element.answers);
        if (this.props.element.input_type == 'ss')
            return this.singleSelect(this.props.element.text, this.props.element.answers);
        if (this.props.element.input_type == 'dt')
            return this.dateQuestion(this.props.element.text);
        if (this.props.element.input_type == 'ot')
            return this.openEndedQuestion(this.props.element.text);
        if (this.props.element.input_type == 'nv')
            return this.numberQuestion(this.props.element.text);
    }

    clickSubmit(e) {
        //Hacky but it was hard to get the jquery-react intergration down
        if (this.props.element.input_type == 'dt') {
            this.props.getNextElement(e, {'answers': [$('.datepicker').val()]});
            $('.datepicker').datepicker('destroy');
        } else {
            this.props.getNextElement(e, {'answers': this.state.selectedAnswers});
        }

        this.setState({
            selectedAnswers: [],
            inputVal: "", 
        })
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
        )
    }
  }

  class ExperimentView extends Component {
    constructor(props) {
      super(props);
      this.state = Object.assign({startClicked:false}, this.props);
    }

    getNextElement(e, params={}) {
       fetch('/experiments/next_phase_element/' + this.props.experiment_id, {
           credentials: 'same-origin',
           method:"POST",
           headers: {
               'Accept': 'application/json',
               'Content-Type': 'application/json'
           },
           body: JSON.stringify(Object.assign({
               currentPhaseId: this.state.phase.id,
               currentElementId: this.state.phase_element.id
           }, params))
       })
           .then(response => response.json())
           .then(json => {
             //global used in conjuction with the Emotiv SDK.
             if (json.finished) {
                fetch('/experiments/gaze_tracking/' + this.state.sessionId, {
                    credentials: 'same-origin',
                    method:"POST",
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({'gazeData': experimentGazeData})
                })
             }
             this.setState({phase: json.phase, phase_element: json.phase_element, finished: json.finished});
           })
       }

    updateDuration(phaseElementId, start, end) {
        const mediaDuration = {
            'elementId': phaseElementId,
            'startTimestamp': start,
            'endTimestamp': end,
        }

        fetch('/experiments/gaze_tracking/phase_element_timestamp/' + this.state.sessionId, {
            credentials: 'same-origin',
            method:"POST",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'phaseElementTimestamps': [mediaDuration]})
        })
    }

    getMediaComponent(phase_element, sessionId) {
       if (phase_element.category_type == 'i') {
           return <ImageElement element={phase_element} getNextElement={this.getNextElement.bind(this)} updateDuration={this.updateDuration.bind(this)} />
       } else if (phase_element.category_type == 'v') {
           return <VideoElement element={phase_element} getNextElement={this.getNextElement.bind(this)} updateDuration={this.updateDuration.bind(this)} />
       } else if (phase_element.category_type == 't') {
           return <TextView element={phase_element} getNextElement={this.getNextElement.bind(this)} updateDuration={this.updateDuration.bind(this)} />
       } else if (phase_element.category_type == 'q') {
           return <QuestionView element={phase_element} getNextElement={this.getNextElement.bind(this)} updateDuration={this.updateDuration.bind(this)} />
       } else if (phase_element.category_type == 'a') {
           return <AudioElement element={phase_element} getNextElement={this.getNextElement.bind(this)} updateDuration={this.updateDuration.bind(this)} />
       }
    }

    startExperimentClicked() {
       fetch('/experiments/start_experiment/' + this.props.experiment_id, {
       credentials: 'same-origin',
       method:"POST",
       headers: {
           'Accept': 'application/json',
           'Content-Type': 'application/json'
       },
       body: JSON.stringify({'screenWidth': document.documentElement.clientWidth, 'screenHeight': document.documentElement.clientHeight})
      }).then(response => response.json())
        .then(json => {
            experimentStarted = true;
            this.setState({startClicked: true, sessionId:json.session_id});
        });
    }

    render() {
        const {experiment_id, phase, phase_element, finished} = this.state;
        const elementView = finished ? (
            <div>
                <h1 id="experiment-success">Thank you</h1>
                <form>
                    <div className="button_input">
                        <button style={{marginTop: "25px"}} formAction="/experiments">Finish</button>
                    </div>
                </form>
            </div>
        ) : this.getMediaComponent(phase_element);

        const start = !this.state.startClicked ? (
            <div className="center_element center">
                <Button id="experiment-button" onClick={this.startExperimentClicked.bind(this)}>Start Experiment</Button>
            </div>
        ) : (
            <div className="content">
                <div style={{
                    display: "flex",
                    flexDirection: "column",
                    borderBottom: "2px solid #ece7e3",
                    paddingBottom: "20px"}}
                >
                    <h1 style={{padding: 0, margin: 0, paddingTop: "20px"}}>
                        {phase.name}
                    </h1>
                </div>
                <div className="center" style={{
                    marginTop: "40px",
                }}>
                    {elementView}
                </div>
            </div>
        );

        return (
            <div>
                {start}
            </div>
        )
    }
  }

  ReactDOM.render(
    <ExperimentView {...experimentViewProps} />,
    document.getElementById("experiment-view")
  );
});
