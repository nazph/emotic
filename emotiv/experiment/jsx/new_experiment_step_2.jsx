/* global requirejs templateNames */

// This file implements the template selection UI.

requirejs(['react', 'reactDOM'], (React, ReactDOM) => {
  const boxMargin = 10;
  const scrollBarWidth = 20;
  const {Component} = React;

  class Templates extends Component {
    constructor(props) {
      super(props);
      this.state = {
        hovered: null,
        search: ''
      };
      this.onClick = this.onClick.bind(this);
    }

    onClick() {
      document.forms[0].submit();
    }

    filteredTemplates() {
      const clean = s => s.trim().toLowerCase();
      const search = clean(this.state.search);
      return this.props.templates.filter(
        t => clean(t[1]).includes(search)
      );
    }

    render() {
      return <div>
        <div
          className="standalone_input_box text_input center_element"
          style={{
            marginBottom: '15px'
          }}
        >
          <input
            id="template_search"
            className="standalone_input_box"
            placeholder="Search"
            value={this.state.search}
            onChange={e => this.setState({search: e.target.value})}
          />
        </div>
        <input
          style={{display: 'none'}}
          type="radio"
          value={this.state.hovered || 0}
          name="template"
          checked="checked"
          readOnly
        />
        <div
          className="center_element center"
          style={{
            maxHeight:
              this.props.boxHeight * 2 + boxMargin * 4 + scrollBarWidth,
            width: this.props.boxWidth * 2 + boxMargin * 4 + scrollBarWidth,
            overflow: 'scroll'
          }}
        >
        {
          this.filteredTemplates().map(t => (
            <div
              key={t[0]}
              className="template_box"
              style={{
                position: 'relative',
                margin: boxMargin,
                width: this.props.boxWidth,
                height: this.props.boxHeight
              }}
              onMouseEnter={() => this.setState({hovered: t[0]})}
              onMouseLeave={() => this.setState({hovered: null})}
            >
              <div
                style={{
                  height: '100%',
                  width: '100%',
                  backgroundColor: 'rgba(0, 0, 0, 0.5)',
                  position: 'absolute',
                  borderRadius: '7px',
                  cursor: 'pointer',
                  display: this.state.hovered === t[0] ? 'flex' : 'none',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                onClick={this.onClick}
              >
                <button
                  className="primary_button"
                  style={{
                    textTransform: 'uppercase',
                    cursor: 'pointer'
                  }}
                  onClick={this.onClick}
                >Select</button>
              </div>
              <div style={{
                height: '80%',
                backgroundColor: '#eb5191'
              }}></div>
              <div style={{
                width: '100%',
                height: '20%',
                textAlign: 'left',
                paddingLeft: '27px',
                lineHeight: `${this.props.boxHeight / 5}px`
              }}>
                {t[1]}
              </div>
            </div>
          ))
        }
        </div>
        <span>{this.filteredTemplates().length} templates to choose from</span>
      </div>;
    }
  }

  ReactDOM.render(
      <Templates
        templates={templateNames}
        boxHeight={250}
        boxWidth={250}
      />,
      document.getElementById('template_container')
  );
});
