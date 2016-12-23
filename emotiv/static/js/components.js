/* global define */

// The functions in this file mirror those in _form_helpers.html. As long as
// both exist, they should be kept in sync.
define([
  'css!fontawesome',
  'es6-polyfill',
  'react',
  'reactDOM',
  'radium'
], (a, b, React, ReactDOM, Radium) => {
  const Button = Radium(({
    children = 'SUBMIT',
    type = 'button',
    className = '',
    style = null,
    clear = false,
    onClick = null,
    buttonStyle = null
  }) => (
    <div
      className={(clear ? 'clear_button_input ' : 'button_input ') + className}
      style={style}
    >
      <button type={type} style={buttonStyle} onClick={onClick}>
        {children}
      </button>
    </div>
  ));

  // Not mirrored in _form_helpers.html.
  const ClearRectButton = Radium(({style, ...props}) => (
    <Button
      clear={true}
      className="center"
      style={[style, {width: '100%'}]}
      buttonStyle={{
        textAlign: 'left',
        padding: '28px 23px',
        borderRadius: '7px',
        width: '100%'
      }}
      {...props}
    />
  ));

  // TODO find a better pop over componenet
  const PopOver = Radium(({style, children, title}) => (
    <button
      type="button"
      class="btn btn-default"
      data-toggle="popover"
      title={title}
      style={style}
      data-content={children}
    >
    </button>
  ));

  // Not mirrored in _form_helpers.html.
  const ModalDialog = Radium(({children, onDismiss, style}) => (
    <div className="dialog_modal" onClick={onDismiss}>
      <div
        className="dialog_modal_box"
        style={[{height: 'unset'}, style]}
        onClick={e => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  ));

  const SelectInput = ({
    name,
    label,
    items,
    checkedItem = 0,
    id = null,
    position = 'standalone',
    style = null
  }) => (
    <div
      style={style}
      className={
        position + '_input_box select_input center_element'
      }
    >
      <select id={id || name} name={name} defaultValue={items[checkedItem][0]}>
        {items.map(item => (
          <option key={item[0]} value={item[0]}>
            {item[1]}
          </option>
        ))}
      </select>
      <label htmlFor={id || name}>{label}</label>
    </div>
  );

  const TextInput = props => <Input {...props} type="text" />;

  // Icon is a shorthand for FontAwesome icons.
  // Not mirrored in _form_helpers.html.
  const Icon = Radium(({fa, ...props}) => (
    <i className={"fa fa-" + fa} aria-hidden="true" {...props}/>
  ));

  const Input = ({label, className = '', inputRef, ...otherProps}) => (
    <div className="standalone_input_box text_input center_element">
      <input
        className={'standalone_input_box ' + className}
        placeholder={label}
        ref={inputRef}
        {...otherProps}
      />
    </div>
  );

  const CheckboxInput = Radium(({
    id,
    name,
    label,
    position = 'standalone',
    style = null,
    labelStyle = null,
    ...otherProps
  }) => (
    <div
      className={position + '_input_box check_input center_element'}
      style={style}
    >
      <input id={id || name} type="checkbox" name={name} {...otherProps} />
      <label htmlFor={id || name} style={labelStyle}>{label}</label>
    </div>
  ));

  const Submit = ({value = 'SUBMIT', className = '', style = null}) => (
    <div className={'submit_input center_element ' + className} style={style}>
      <input type="submit" name="submit" value={value} />
    </div>
  );

  const TextArea = ({
    name,
    label,
    position = 'standalone',
    textareaRef = null,
    value = null
  }) => (
    <div
      className={position + '_input_box text_input center_element'}
      style={{border: 'none'}}
    >
      <textarea
        className={position + '_input_box'}
        name={name}
        ref={textareaRef}
        placeholder={label}
      >
        {value}
      </textarea>
    </div>
  );

  const Dots = ({total = 6, active}) => <div>
    {
      new Array(total).fill(0).map((_, i) => (
        i === active - 1 ?
          <Icon
            key={i} style={{color: '#3A3F49', margin: '0 2px'}} fa="circle"
          /> :
          <Icon
            key={i} style={{color: '#A6A5A9', margin: '0 2px'}} fa="circle-o"
          />
      ))
    }
  </div>;

  return {
    Button,
    CheckboxInput,
    ClearRectButton,
    Dots,
    Icon,
    Input,
    ModalDialog,
    SelectInput,
    Submit,
    TextArea,
    TextInput,
    PopOver
  };
});
