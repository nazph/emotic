/* global define _es6 */

// This file implements two of the screens for experiment creation,
// which are both about selecting user attributes.

define([
  'jquery-ui', // for datepicker
  'css!fontawesome',
  'es6-polyfill',
  'typeahead-addresspicker.min',
  'jquery',
  'react',
  'reactDOM',
  _es6('components')
], (a, b, c, AddressPicker, $, React, ReactDOM, components) => {
  const {
    Button,
    CheckboxInput,
    ClearRectButton,
    Dots,
    Input,
    TextArea,
    TextInput,
    Submit
  } = components;
  const {Component} = React;

  class CriteriaForm extends Component {
    constructor(props) {
      super(props);
      this.state = {
        displayed: this.props.initialDisplayed,
        showCriteriaModal: false
      };
    }

    render() {
      const {attributes, newExperiment, forStep} = this.props;
      const filters = this.props.filters ||
        attributes.map(a => ({attribute: a}));
      const {displayed, showCriteriaModal} = this.state;
      const hidden = filters
        .map(f => f.attribute)
        .filter(a => !displayed.includes(a.id));
      const filterForAttr = id => {
        for (let i = 0; i < filters.length; i++) {
          let f = filters[i];
          if (f.attribute.id === id) {
            return [f, i];
          }
        }
        return [null, null];
      };
      return <div
        className="center_element center"
        style={{
          display: 'inline-block',
          width: '430px'
        }}
      >
      {
        displayed.map(id => filterForAttr(id)).map(([f, i]) => (
          <CriteriaBox
            key={`${i}-${f.attribute.id}`}
            prefix={`filters-${i}-p-`}
            params={f.params}
            attrInput={`filters-${i}-attribute_id`}
            attribute={f.attribute}
            showDetail={forStep === 3}
          />
        ))
      }
      {
        hidden.length === 0 ? null : (
          <div
            className="drop_down"
            style={{
              width: '100%',
              marginBottom: '17px'
            }}
          >
            <ClearRectButton>
              Add Additional Criteria
              <i
                className="fa fa-caret-down"
                style={{float: 'right'}}
                aria-hidden={true}
              />
            </ClearRectButton>
            <div className="drop_down-content" style={{width: '100%'}}>
              {
                hidden.map(a => (
                  <li
                    key={a.id}
                    onClick={() => {
                      this.setState({displayed: displayed.concat(a.id)});
                    }}
                  >
                    {a.name}
                  </li>
                ))
              }
            </div>
          </div>
        )
      }
      <ClearRectButton
        onClick={() => this.setState({showCriteriaModal: true})}
        style={{marginBottom: '17px'}}
      >
        I'd like to request new criteria
        <i
          className="fa fa-plus-square"
          style={{float: 'right'}}
          aria-hidden={true}
        />
      </ClearRectButton>
      <br />
      <Submit value={newExperiment ? 'NEXT' : 'SAVE'} />
      { newExperiment ? <br /> : null }
      { newExperiment ? <Dots total={6} active={3} /> : null }
      {
        showCriteriaModal ? (
          <div
            className="dialog_modal"
            onClick={() => this.setState({showCriteriaModal: false})}
          >
            <div
              className="dialog_modal_box"
              onClick={e => e.stopPropagation()}
              style={{
                height: '480px',
                width: '600px'
              }}
            >
              <h2>Request new criteria</h2>
              <input
                id="delay_release"
                name="delay_release"
                type="checkbox"
                defaultChecked={true}
              />
              <label htmlFor="delay_release">Delay releasing experiment until
                new criteria is considered by Emotiv Admin</label>
              <TextArea name="criteria_suggestion" />
              <Submit value="SUBMIT REQUEST"/>
            </div>
          </div>
        ) : null
      }
      </div>;
    }
  }

  // CriteriaBox is the view of a single attribute or criteria.
  //
  // It can be rendered as just the name of the attribute, or it can include
  // a detail view to specify what attribute values to accept.
  class CriteriaBox extends Component {
    constructor(props) {
      super(props);
      this.state = {enabled: true};
    }

    render() {
      const {
        prefix, params, showDetail, attribute, attrInput
      } = this.props;
      const fontSize = 15;
      return <div>
        {
          this.state.enabled ?
            <input
              type="hidden"
              name={attrInput}
              value={attribute.id}
            /> :
            null
        }
        <div
          className="center_element criteria_box"
          id={this.props.id}
          style={(() => {
            let isText = attribute.input_type === 'ot';
            let isLocation = attribute.name === 'Location';
            if (isText && isLocation) {
              return {overflow: 'visible'};
            }
            if (isText) {
              return {display: 'none'};
            }
            return null;
          })()}
        >
          <div className="top_input_box check_input center_element">
            <div>
              <input
                type="checkbox"
                id={attribute.name}
                name="attributes"
                value={attribute.id}
                checked={this.state.enabled ? "checked" : ""}
                onChange={() => this.setState({
                  enabled: !this.state.enabled
                })}
              />
              <label
                htmlFor={attribute.name}
                style={{
                  fontSize: fontSize,
                  textAlign: 'middle'
                }}
              >
                {attribute.name}
              </label>
            </div>
          </div>
          {
            this.state.enabled && showDetail ? (
              <div
                className="check_input center_element"
                style={{
                  display: 'inline-flex',
                  flexWrap: 'wrap',
                  padding: 0,
                  margin: 0,
                  backgroundColor: '#f6f6f7'
                }}
              >
              {(() => {
                switch (attribute.input_type) {
                  case 'ms':
                  case 'ss':
                    return <SelectAttribute
                      prefix={prefix}
                      fontSize={fontSize + 1}
                      options={attribute.possible_options}
                      params={params}
                    />;
                  case 'nm':
                    return <NumericAttribute
                      prefix={prefix}
                      params={params}
                    />;
                  case 'dt':
                    return <DateAttribute
                      prefix={prefix}
                      params={params}
                    />;
                  case 'ot':
                    return <LocationAttribute
                      prefix={prefix}
                      params={params}
                    />;
                  default:
                    return null;
                }
              })()}
              </div>
            ) :
            null
          }
        </div>
      </div>;
    }
  }

  // SelectAttribute is the view for single-select and multi-select attributes.
  class SelectAttribute extends Component {
    constructor(props) {
      super(props);
      this.state = {
        checked: props.options.map(
           o => props.params.selected.includes(o.id)
        )
      };
      this.onChange = this.onChange.bind(this);
    }

    onChange(i) {
      let c = this.state.checked;
      c[i] = !c[i];
      this.setState({checked: c});
    }

    render() {
      const {fontSize, options, prefix} = this.props;
      return <div
        className="check_input center_element"
        style={{
          display: 'inline-flex',
          flexWrap: 'wrap',
          padding: 0,
          margin: 0,
          backgroundColor: '#f6f6f7'
        }}
      >{
        options.map((o, i) => (
          <div
            key={o.id}
            style={{
              flex: '1 1 120px',
              flexBasis: '120px',
              minWidth: o.value.length * fontSize * .8,
              maxWidth: '430px',
              lineHeight: '40px',
              height: '40px',
              borderLeft: 'solid thin #e4e4e6',
              borderTop: 'solid thin #e4e4e6',
              padding: '25px 17px'
            }}
          >
            <input
              id={`check_${o.id}`}
              type="checkbox"
              className="eye_input"
              name={prefix + 'selected'}
              value={o.id}
              onChange={() => this.onChange(i)}
              checked={this.state.checked[i]}
            />
            <label
              htmlFor={`check_${o.id}`}
              style={{fontSize: fontSize}}
            >
              {o.value}
            </label>
          </div>
      ))
      }</div>;
    }
  }

  class NumericAttribute extends Component {
    constructor(props) {
      super(props);
      this.state = {
        low: this.props.params.low,
        high: this.props.params.high
      };
    }

    render() {
      return <div>
        <Input
          name={this.props.prefix + 'low'}
          label="Lowest allowed. Leave blank for no cutoff."
          type="number"
          value={this.state.low}
          onChange={e => this.setState({low: e.target.value})}
        />
        <Input
          name={this.props.prefix + 'high'}
          label="Highest allowed. Leave blank for no cutoff."
          type="number"
          value={this.state.high}
          onChange={e => this.setState({high: e.target.value})}
        />
      </div>;
    }
  }

  class DateAttribute extends Component {
    componentDidMount() {
      $(".datepicker").datepicker({
        dateFormat: "yy-mm-dd"
      });
    }

    render() {
      return (
        <div style={{
          display: 'flex',
          width: '100%',
          backgroundColor: 'white',
          justifyContent: 'space-between',
          padding: '0 10px 20px 10px'
        }}>
          <DateInput
            name={this.props.prefix + 'low'}
            placeholder="Select earliest date"
            defaultValue={this.props.params.low}
          />
          <DateInput
            name={this.props.prefix + 'high'}
            placeholder="Select latest date"
            defaultValue={this.props.params.high}
          />
        </div>
      );
    }
  }

  const DateInput = props => (
      <div
        className="standalone_input_box text_input center_element"
        style={{
          display: 'inline-block',
          width: '45%'
        }}
      >
        <input
          className="standalone_input_box datepicker"
          style={{
            width: '100%',
            paddingLeft: 0,
            paddingRight: 0,
            textAlign: 'center'
          }}
          {...props}
        />
      </div>
  );

  class LocationAttribute extends Component {
    componentDidMount() {
      $('#address').typeahead({highlight: true}, {
        displayKey: 'description',
        source: new AddressPicker().ttAdapter()
      });
    }

    render() {
      return <Input
        name={this.props.prefix + 'text'}
        label="Place name. Leave blank to allow any location."
        id="address"
        type="address"
        defaultValue={this.props.params.text}
      />;
    }
  }

  return {
    render: props => {
      ReactDOM.render(
        <CriteriaForm {...props} />,
        document.getElementById('criteria_form')
      );
    }
  };
});
