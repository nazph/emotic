/* global requirejs _es6 elements submit_element is_admin, token, upload_file,
 * allowed_image_extensions, allowed_audio_extensions, allowed_video_extensions
 * */

// This file implements the view for editing a phase.

requirejs([
  'css!fontawesome',
  'es6-polyfill',
  'whatwg-fetch',
  'filepicker',
  'react',
  'reactDOM',
  'radium',
  _es6('components'),
  _es6('sortable')
], (a, b, c, filepicker, React, ReactDOM, Radium, Components, Sortable) => {
  const {Component} = React;
  const {
    Button, ClearRectButton, SelectInput, TextInput, TextArea
  } = Components;
  const {SortableContainer} = Sortable;
  const {update} = React.addons;

  const QUESTION = 'q';
  const WEBSITE = 'w';
  const LIKERT = 'l';
  const AUDIO = 'a';
  const IMAGE = 'i';
  const TEXT = 't';
  const VIDEO = 'v';

  let test_enable_hovers = false;

  // http://stackoverflow.com/a/2117523/3072514
  function guid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0;
      var v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  // PickMediaController is a container component for media selection.
  // See "Presentational and Container Components":
  //
  //  https://medium.com/@dan_abramov/smart-and-dumb-components-7ca2f9a7c7d0#.610esx8ds
  class PickMediaController extends Component {
    constructor(props) {
      super(props);
      this.state = {loading: true, media: []};
    }

    componentDidMount() {
      fetch('/material/available/' + this.props.contentType, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authentication-Token': token
        }
      })
        .then(response => response.json())
        .then(data => this.setState(update(this.state, {
          loading: {$set: false},
          media: {$unshift: data.media}
        }))).catch(console.log);
    }

    render() {
      return <PickMedia
        {...this.props}
        {...this.state}
        onUpload={data => this.setState(update(this.state, {
          media: {
            $push: [data]
          }
        }))}
      />;
    }
  }

  // PickMedia is the view for selecting audio, video, or images.
  const PickMedia = ({
    onSubmit,
    onUpload,
    mediaPlural,
    loading,
    contentType,
    extensions,
    media
  }) => <div>
    <div className="button_input center_element">
      <button
        style={{paddingLeft: 8, paddingRight: 8}}
        onClick={e => {
          e.preventDefault();
          filepicker.pickAndStore(
            {
              multiple: false,
              extensions: extensions,
              services: ['COMPUTER', 'URL']
            },
            {},
            Blobs => fetch('/material/record_filestack_upload', {
              method: 'POST',
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authentication-Token': token
              },
              body: JSON.stringify({
                content_type: contentType,
                url: Blobs[0].url
              })
            })
              .then(response => response.json())
              .then(onUpload)
              .catch(console.log)
          );
        }}
      >
        Select File
      </button>
    </div>
    <br/>
    {loading ?
      'Loading...' :
      media.length > 0 && <div>
        {mediaPlural}:
        <select name="material" defaultValue={media.slice(-1)[0].id}>
          {media.map(m => (
            <option value={m.id} key={m.id}>
              {m.name}
            </option>
          ))}
        </select>
      </div>
    }
    <br/>
    {contentType === 'i' && <div>
      How long should it be displayed?
      <div><small>(in milliseconds)</small></div>
      <input
        className="standalone_input_box"
        type="number"
        name="duration_ms"
      />
    </div>}
    <br/>
    <input type="hidden" name="category_type" value={contentType}/>
    <div>
      <Button onClick={onSubmit}/>
    </div>
  </div>;

  // autofocus is a succinct way to express that an element should receive
  // focus when it is first rendered. Use it by setting it as the value of
  // the "ref" prop on the element in question.
  function autofocus(ref) {
    if (ref) {
      ref.focus();
    }
  }

  // NewElementModal is the view we present when a user clicks "New Element".
  // It lets them select the type of the new elemenent and some other properties
  class NewElementModal extends Component {
    constructor(props) {
      super(props);
      this.state = {inputType: '', errors: []};
      this.onSubmit = this.onSubmit.bind(this);
    }

    onSubmit(event) {
      if (event) {
        event.preventDefault();
      }
      this.setState({errors: []});
      var element = $(this.form)
        .serializeArray()
        .reduce((x, o) => {
          x[o.name] = o.value;
          return x;
        }, {});
      if (['q', 't'].indexOf(element.category_type) > -1 && !element.text) {
        this.setState({errors: ['Text or Question: This field is required.']});
        return;
      }
      if (element.category_type === 'i' && !element.duration_ms) {
        this.setState({errors: ['Duration: This field is required.']});
        return;
      }
      if (element.category_type === 'i' &&
          !/^[0-9]+$/.test(element.duration_ms)) {
        this.setState({
          errors: ['Duration: This field must be a positive whole number.']
        });
        return;
      }
      if (['a', 'i', 'v'].indexOf(element.category_type) > -1) {
        $.ajax({
          type: 'GET',
          url: '/material/filename?id=' + element.material,
          success: data => {
            element.material_data = data;
            this.props.onNewElement(element);
            this.props.onClose();
          }
        });
        return;
      }
      this.props.onNewElement(element);
      this.props.onClose();
    }

    render() {
      return (
        <div className="element_dialog_modal" style={{display: 'block'}}>
            <div className="element_dialog_modal_box">
                <div>
                    <h2>New Phase Element</h2>
                </div>
                {this.state.inputType === '' &&
                  <div>
                    {['Text', 'Video', 'Image', 'Audio', 'Question', 'Likert', 'Website Activity'].map(t => (
                      <div
                        key={t}
                        className="element_type_selector"
                        onClick={_ => this.setState({inputType: t})}>
                          <div className="element_type_name">
                            {t}
                          </div>
                          <div className="element_type_arrow"></div>
                      </div>
                    ))}
                  </div>
                }
                <ul className="flashes">
                  {this.state.errors.map((text, i) => (
                    <div
                      key={i}
                      className="center_element center alert alert-danger"
                    >
                      <li className="error">
                        {text}
                      </li>
                    </div>
                  ))}
                </ul>
                <form
                  onSubmit={this.onSubmit}
                  ref={ref => {
                    if (ref) {
                      this.form = ref;
                    }
                  }}
                >
                  {(_ => {
                    switch (this.state.inputType) {
                      case 'Website Activity':
                        return <div>
                          <br/>
                          <TextArea
                            name="description"
                            label="Enter a description of the activity"
                            textareaRef={autofocus}
                          />
                          <br/>
                          <TextArea
                            name="text"
                            label="Enter the url that your users will be redirected to"
                            textareaRef={autofocus}
                          />
                          <br/>
                          <input type="hidden" name="category_type" value="w"/>
                          <Button onClick={this.onSubmit}/>
                      </div>;
                      case 'Text':
                        return <div>
                          <br/>
                          <TextArea
                            name="text"
                            label="Text"
                            textareaRef={autofocus}
                          />
                          <br/>
                          <input type="hidden" name="category_type" value="t"/>
                          <Button onClick={this.onSubmit}/>
                        </div>;
                      case 'Video':
                        return <PickMediaController
                          onSubmit={this.onSubmit}
                          mediaPlural="Video Files"
                          contentType="v"
                          extensions={allowed_video_extensions}
                        />;
                      case 'Audio':
                        return <PickMediaController
                          onSubmit={this.onSubmit}
                          mediaPlural="Audio Files"
                          contentType="a"
                          extensions={allowed_audio_extensions}
                        />;
                      case 'Image':
                        return <PickMediaController
                          onSubmit={this.onSubmit}
                          mediaPlural="Images"
                          contentType="i"
                          extensions={allowed_image_extensions}
                        />;
                      case 'Question':
                        return <div>
                          <TextInput
                            name="text"
                            label="Enter a question"
                            inputRef={autofocus}
                          />
                          <br/>
                          <SelectInput
                            name="input_type"
                            label="Input Type"
                            items={[
                              ['ss', 'Single-select multiple choice'],
                              ['ms', 'Multi-select multiple choice'],
                              ['dt', 'datetime'],
                              ['ot', 'open text'],
                              ['nv', 'numeric value']
                            ]}
                            style={{width: 430}}
                          />
                          <br/>
                          <input type="hidden" name="category_type" value="q"/>
                          <Button onClick={this.onSubmit}/>
                        </div>;
                      case 'Likert':
                        return <div>
                            <TextInput
                              name="text"
                              label="Enter a question"
                              inputRef={autofocus}
                            />
                            <br/>
                            <Button onClick={this.onSubmit}/>
                            <input type="hidden" name="category_type" value="l"/>
                          </div>;
                      default:
                        return null;
                    }
                  })()}
                </form>
                <br/>
                <div
                  className="clear_button_input"
                  onClick={this.props.onClose}
                >
                  <button type="button">
                    <div className="clear_button_input_text">
                      Cancel
                    </div>
                  </button>
                </div>
            </div>
        </div>
      );
    }
  }

  // PhaseDetail is the top-level component for this page.
  @Radium
  class PhaseDetail extends Component {
    constructor(props) {
      super(props);
      this.state = Object.assign(props.initialState, {
        showElementModal: false
      });
      this.addElement = this.addElement.bind(this);
      this.savePhase = this.savePhase.bind(this);
    }

    addElement(newElement) {
      if (newElement.category_type === QUESTION && !newElement.answers) {
        newElement = update(newElement, {answers: {$set: []}});
      }
      if (newElement.category_type === LIKERT && !newElement.answers) {
        newElement = update(newElement, {answers: {$set: [
          {id: guid(), value: 1, label: 'Strongly Disagree'},
          {id: guid(), value: 2, label: 'Disagree'},
          {id: guid(), value: 3, label: 'Neither Agree nor Disagree'},
          {id: guid(), value: 4, label: 'Agree'},
          {id: guid(), value: 5, label: 'Strongly Agree'}
        ]}});
      }
      this.setState(state => update(state, {
        elements: {
          $push: [update(newElement, {
            id: {
              $set: guid()
            }
          })]
        }
      }));
    }

    savePhase() {
      document.getElementById("main_form").submit();
    }

    render() {
      console.log(this.state.elements);
      const {elements, currentElement, showElementModal} = this.state;
      const boxStyle = {
        width: '200px',
        height: '150px',
        marginBottom: 10,
        marginRight: 10,
        boxSizing: 'border-box',
        borderRadius: '7px'
      };
      const sidebarBorder = 'thin solid grey';
      const postData = update(this.state, {currentElement: {$set: undefined}});
      const {readOnly} = this.props;
      return <div style={{display: 'flex', height: '100%'}}>
        {showElementModal &&
          <NewElementModal
            onClose={_ => this.setState({showElementModal: false})}
            onNewElement={this.addElement.bind(this)}
          />
        }
        <form style={{display: 'none'}} method="POST" id="main_form">
          <input type="hidden" name="data" value={JSON.stringify(postData)}/>
        </form>
        <div style={{
          width: '235px',
          height: '100%',
          borderRight: sidebarBorder
        }}>
          <SortableContainer
            id="element_cards"
            style={{
              maxHeight: 600,
              overflowY: 'scroll',
              marginBottom: boxStyle.marginBottom,
              marginRight: boxStyle.marginRight
            }}
            enabled={!readOnly}
            moveCard={(from, to) => this.setState(update(this.state, {
              elements: {$splice: [
                [from, 1],
                [to, 0, elements[from]]
              ]}
            }))}>
            {
              elements.map((e, i) => (
                <ElementCard
                  key={e.id}
                  boxStyle={boxStyle}
                  onSelect={_ => this.setState({currentElement: e.id})}
                  readOnly={readOnly}
                  onDelete={_ => this.setState({
                    currentElement: e.id === currentElement ?
                      null : currentElement,
                    elements: update(elements, {$splice: [[i, 1]]})
                  })}
                  element={e}
                />
              ))
            }
          </SortableContainer>
          {readOnly || (<div>
            <div
                style={[boxStyle, {
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: 25,
                  color: '#B6B5B6',
                  border: '2px solid #B6B5B6',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }]}
                onClick={_ => this.setState({showElementModal: true})}>
              <i
                style={{marginBottom: 5}}
                className="fa fa-plus-circle fa-2x"
                aria-hidden="true"></i>
              New Element
            </div>
            {elements.length > 1 && (
              <div style={{
                height: '100px',
                paddingTop: 10,
                paddingRight: 30,
                borderTop: sidebarBorder,
                fontSize: 'smaller'
              }}>
                Drag elements to rearrange their order.
              </div>
            )}
          </div>)}
        </div>
        <div id="phase_content" style={{width: '100%', height: '100%'}}>
          {(_ => {
            if (elements.length === 0) {
              return <div><h1 style={{textAlign: 'center'}}>
                No elements added to phase yet.
              </h1></div>;
            }
            if (currentElement === null) {
              return null;
            }
            const i = elements.findIndex(e => e.id === currentElement);
            const p = elements[i];
            const style = {width: 433, margin: '77px auto 0 auto'};
            switch (p.category_type) {
              case QUESTION:
                return <QuestionElement
                  style={style}
                  element={p}
                  readOnly={readOnly}
                  onChange={newEl => this.setState({elements: update(
                      elements, {[i]: {$set: newEl}})
                  })}
                />;
              case LIKERT:
                return <LikertElement
                  style={style}
                  element={p}
                  readOnly={readOnly}
                  onChange={newEl => this.setState({elements: update(
                      elements, {[i]: {$set: newEl}})
                  })}/>;
              case WEBSITE:
                return <div style={style}>
                  <h3 style={{textAlign: 'center'}}>{p.description}</h3>
                  <h5><a style={{textAlign: 'center'}} href={p.text}>{p.text}</a></h5>
                </div>;
              case TEXT:
                return <div style={style}>
                  <h1 style={{textAlign: 'center'}}>{p.text}</h1>
                </div>;
              case AUDIO:
                return <div style={style}>
                  <h1 style={{textAlign: 'center'}}>Audio clip</h1>
                  <h2 style={{textAlign: 'center'}}>{p.material_data.name}</h2>
                </div>;
              case VIDEO:
                return <div style={style}>
                  <h1 style={{textAlign: 'center'}}>Video</h1>
                  <h2 style={{textAlign: 'center'}}>{p.material_data.name}</h2>
                  <video
                    src={p.material_data.file_name}
                    width={style.width}
                    controls
                  />
                </div>;
              case IMAGE:
                return <div style={style}>
                  <h2 style={{textAlign: 'center'}}>{p.material_data.name}</h2>
                  <div style={{
                    height: style.width,
                    backgroundImage: `url(${p.material_data.file_name})`,
                    backgroundSize: 'contain',
                    backgroundRepeat: 'no-repeat'
                  }}/>
                </div>;
              default:
                return <span>Phase view not implemented</span>;
            }
          })()}
        </div>
      </div>;
    }
  }

  // ElementCard implements the view of a phase element in the card list.
  @Radium
  class ElementCard extends Component {
    render() {
      const {
        boxStyle, onSelect, onDelete, element, readOnly, ...other
      } = this.props;
      /* Chrome has a bug in the interaction between drag-and-drop and the :hover
       * CSS selector. See the tracker here:
       *
       *   https://bugs.chromium.org/p/chromium/issues/detail?id=410328
       *
       * The upshot is that relying on :hover to determine when to render the
       * delete button will cause our UI to look weird when this component is
       * dragged.
       *
       * As a workaround, we can rely on Radium to do the same thing that :hover
       * would do.
       */
      const cardStyle = {
        height: '100%',
        padding: '25px 20px',
        boxSizing: 'border-box',
        color: '#8F9395',
        backgroundColor: '#D7D8D6',
        borderRadius: 'inherit'
      };
      const outlinedTextStyle = {
        color: 'white',
        textShadow: '1px 0 0 #000, 0 -1px 0 #000, 0 1px 0 #000, -1px 0 0 #000'
      };
      return <div
          style={[boxStyle, {
            'position': 'relative',
            ':hover': {} // Tell Radium to track :hover state...
          }]}
          key="workaroundKey" // ...for the element with this key.
          onClick={onSelect}
        >{(_ => {
          switch (element.category_type) {
            case QUESTION:
              return <div style={[cardStyle, {
                backgroundColor: '#555962',
                color: '#B1B3B3',
                borderRadius: 'inherit'
              }]}>
                <span>
                    Question {(_ => {
                      switch (element.input_type) {
                        case 'ss':
                        case 'ms':
                          return ' (multiple choice)';
                        case 'dt':
                          return ' (datetime)';
                        case 'ot':
                          return ' (open text)';
                        case 'nv':
                          return ' (numeric value)';
                        default:
                          return '';
                      }
                    })()}
                </span>
                <div style={{color: 'white'}}>{element.text}</div>
              </div>;
            case LIKERT:
              return <div style={[cardStyle, {
                backgroundColor: '#555962',
                color: '#B1B3B3',
                borderRadius: 'inherit'
              }]}>
                <span> Likert Question </span>
                <div style={{color: 'white'}}>{element.text}</div>
              </div>;
            case AUDIO:
              return <div style={cardStyle}>Audio</div>;
            case IMAGE:
              return <div style={[cardStyle, outlinedTextStyle, {
                borderRadius: 'inherit',
                backgroundImage: `url(${element.material_data.file_name})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center'
              }]}>
                Image
              </div>;
            case VIDEO:
              return <div style={[cardStyle, {
                position: 'relative',
                zIndex: 0
              }]}>
                <span style={[outlinedTextStyle, {
                  position: 'relative',
                  zIndex: 10
                }]}>Video</span>
                <video
                  src={element.material_data.file_name + '#t=1'}
                  style={{
                    width: '100%',
                    height: '100%',
                    position: 'absolute',
                    left: 0,
                    top: 0
                  }}
                />
              </div>;
            case WEBSITE:
              return <div style={cardStyle}>
              <span>Website Activity</span>
              <div>{element.text}</div>
              <div>{element.description}</div>
            </div>;
            case TEXT:
              return <div style={cardStyle}>
                <span>Text</span>
                <div>{element.text}</div>
              </div>;
            default:
              return null;
          }
        })()}

        {/*
         * Radium workaround: Only render this div when Radium says its
         * parent is hovered. The "hover_modal" class does this as well,
         * but is subject to the bug mentioned above.
         *
         * This is also a test workaround. Mousing over this element with
         * Selenium fails to trigger the hover state, with or without Radium,
         * so in tests we'll always show the modal.
         */}
        {(
          test_enable_hovers ||
          Radium.getState(this.state, 'workaroundKey', ':hover')
         ) && !readOnly && (
          <div className="hover_modal force_hover_modal">
            <div
              className="phase_hover"
              style={{justifyContent: 'flex-end'}}>
              <button
                style={{
                  width: '65%',
                  height: '32px',
                  marginBottom: 18,
                  backgroundColor: 'rgba(0, 0, 0, 0.6)'
                }}
                onClick={e => {
                  e.stopPropagation();
                  onDelete();
                }}
                className="phase_edit_button">
                Delete
              </button>
            </div>
          </div>
        )}

      </div>;
    }
  }

  @Radium
  class LikertElement extends Component {
    render() {
      const {style, element, onChange, readOnly} = this.props;
      const margin = '12px';
      const answerHeight = '60px';
      return <div style={style}>
        <h1 style={{
          textAlign: 'center',
          color: 'black',
          marginBottom: 38
        }}>
          {element.text}
        </h1>
        <div
          className="element_question_answers"
          style={{
            width: '100%',
            marginBottom: margin
          }}
        >{
          element.answers.map((c, i) => (
            <div
              key={c.id}
              style={{height: answerHeight}}
              className="element_question_answer">
              <TextInput
                style={{paddingLeft: 25, lineHeight: answerHeight}}
                className="element_question_answer_value"
                name="value"
                label={c.label}
                inputRef={autofocus}
                value={c.label}
                onChange={e => {
                  let newAnswers = element.answers;
                  newAnswers[i] = {...newAnswers[i], label: e.target.value};
                  return onChange(
                    update(element, {answers: {$set: newAnswers}})
                  );
                }}
              />
            </div>
          ))
        }</div>
      </div>;
    }
  }
  // QuestionElement is the large detail view for question elements.
  @Radium
  class QuestionElement extends Component {
    constructor(props) {
      super(props);
      this.state = {
        showRowModal: false,
        showConditionalModal: false,
        validationError: false,
        newAnswer: '',
        newInputType: ''
      };
      this.handleSubmit = this.handleSubmit.bind(this);
      this.destroyModal = this.destroyModal.bind(this);
    }

    handleSubmit(e) {
      e.preventDefault();
      const {onChange, element} = this.props;
      const {newAnswer, newInputType} = this.state;
      if (!newAnswer) {
        this.setState({validationError: true});
        return;
      }
      onChange(update(element, {answers: {$push: [{
        content_type: newInputType,
        value: newAnswer,
        id: guid()
      }]}}));
      this.destroyModal();
    }

    destroyModal() {
      this.setState({
        showRowModal: false,
        showConditionalModal: false,
        newAnswer: '',
        validationError: false
      });
    }

    render() {
      const {style, element, onChange, readOnly} = this.props;
      const {newAnswer, showRowModal, showConditionalModal, newInputType} = this.state;
      const margin = '12px';
      const answerHeight = '60px';
      const imageHeight = '200px';
      const header = <h1 style={{
        textAlign: 'center',
        color: 'black',
        marginBottom: 38
      }}>
        {element.text}
      </h1>;
      if (!['ss', 'ms'].includes(element.input_type)) {
        return <div style={style}>{header}</div>;
      }
      return <div style={style}>
        {header}
        <div
          className="element_question_answers"
          style={{
            width: '100%',
            marginBottom: margin
          }}
        >{
          element.answers.map((c, i) => (
            <div
              key={c.id}
              style={{height: c.content_type === 't' ? answerHeight : imageHeight}}
              className="element_question_answer">
              {c.content_type === 't' ?
                <div
                  style={{paddingLeft: 25, lineHeight: answerHeight}}
                  className="element_question_answer_value">
                  {c.value}
                </div> :
                <img style={{
                  maxWidth: '100%',
                  maxHeight: '100%',
                  verticalAlign: 'middle'
                }} src={c.value} alt=""/>
              }

              {readOnly || (
                <div className="element_question_answer_delete">
                  <span
                    style={{
                      display: 'inline-block',
                      fontSize: '25px',
                      color: 'lightgray',
                      lineHeight: answerHeight,
                      transform: 'rotate(0.125turn)',
                      cursor: 'pointer'
                    }}
                    onClick={_ => onChange(
                        update(element, {answers: {$splice: [[i, 1]]}})
                    )}
                  >
                    +
                  </span>
                </div>
              )}
            </div>
          ))
        }</div>
        {readOnly || (<div>
          <ClearRectButton
            style={{
              marginBottom: margin
            }}
            onClick={_ => this.setState({
              showRowModal: true,
              newInputType: 't'
            })}
          >
            <i
              className="fa fa-plus-square"
              style={{marginRight: 12}}
              aria-hidden={true} />
            Add additional text options
          </ClearRectButton>
          <ClearRectButton
            style={{
              marginBottom: margin
            }}
            onClick={_ => this.setState({
              showRowModal: true,
              newInputType: 'i'
            })}
          >
            <i
              className="fa fa-plus-square"
              style={{marginRight: 12}}
              aria-hidden={true} />
            Add additional image option
          </ClearRectButton>
          <ClearRectButton
            onClick={_ => this.setState({showConditionalModal: true})}
          >{
            element.conditional ?
              'Modify Conditional' :
              <div style={{display: 'flex', justifyContent: 'space-between'}}>
                <span>Add a conditional to this element</span>
                <i className="fa fa-plus-square" aria-hidden={true} />
              </div>
          }</ClearRectButton>
          {
            showRowModal ? (
              <div
                className="element_answer_dialog_modal"
                style={{display: 'block'}}
                onClick={this.destroyModal}
              >
                <div
                  className="element_dialog_modal_box"
                  onClick={e => e.stopPropagation()}
                >
                  <h2>New Question Answer</h2>
                  {this.state.validationError && (
                    <ul className="flashes">
                      <div className="center_element center alert alert-danger">
                        <li className="error">
                          value: This field is required.
                        </li>
                      </div>
                    </ul>
                  )}
                  <form onSubmit={this.handleSubmit} id="element_answer_form">
                    <TextInput
                      name="value"
                      label={newInputType === 't' ? 'Enter question text' : 'Enter image url'}
                      inputRef={autofocus}
                      value={newAnswer}
                      onChange={e => this.setState({newAnswer: e.target.value})}
                    />
                    <br/>
                    <Button type="submit" />
                    <br/>
                  </form>
                  <br/>
                  <div className="clear_button_input">
                    <button type="button" onClick={this.destroyModal}>
                      <div className="clear_button_input_text">Cancel</div>
                    </button>
                  </div>
                </div>
              </div>
            ) : null
          }
          {
            showConditionalModal ? (
              <div
                className="element_answer_dialog_modal"
                style={{display: 'block'}}
                onClick={_ => this.setState({showConditionalModal: false})}
              >
                <div
                  className="element_dialog_modal_box"
                  onClick={e => e.stopPropagation()}
                >
                  <h2>Not implemented yet</h2>
                  <Button
                    onClick={_ => this.setState({showConditionalModal: false})}
                    clear={true}>
                    Close
                  </Button>
                </div>
              </div>
            ) : null
          }
        </div>)}
      </div>;
    }
  }

  const detailView = ReactDOM.render(
    <PhaseDetail
      initialState={{
        currentElement: elements.length > 0 ? elements[0].id : null,
        elements: elements
      }}
      readOnly={is_admin}
    />,
    document.getElementById('react_content')
  );

  window.save_phase = detailView.savePhase;
  window.test_hook_enable_hovers = function() {
    test_enable_hovers = true;
    detailView.forceUpdate();
  };
  filepicker.setKey('A9LPQU0OtQuqh04xrhojmz');
});
