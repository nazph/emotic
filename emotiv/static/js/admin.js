/* global define _es6 */

// This file implements one component on the admin dashboard page.
// The admin dashboard page mostly doesn't use React yet.

define(['react', _es6('components')], (React, {Button}) => {
  const buttonProps = {
    style: {display: 'inline-block'},
    buttonStyle: {width: 140}
  };
  return {
    DecisionModal: ({
      handleClose,
      handleDecision,
      approve,
      organization,
      name,
      isExperiment,
      id
    }) => {
      const decide = approve ? 'Approve' : 'Deny';
      const kind = isExperiment ? 'experiment' : 'attribute';
      return <div className="dialog_modal" onClick={handleClose}>
        <div
          style={{width: 400, height: 400}}
          className="dialog_modal_box"
          onClick={e => e.stopPropagation()}
        >
          <h2>{decide} this {kind}?</h2>
          {isExperiment ? <p>Organization: {organization}</p> : null}
          <p>
            {
              isExperiment ? 'Experiment Title' : 'Attribute Description'
            }: {name}
          </p>
          <form
            method="post"
            action={
              `/admin/${approve ? 'approve' : 'deny'}/${kind}/${id}`
            }
          >
            <div
              className="standalone_input_box text_input center_element"
              style={{
                display: approve ? 'none' : null,
                border: 'none',
                width: '90%'
              }}>
              <textarea
                className="standalone_input_box"
                style={{width: '90%', marginBottom: 15}}
                name="comment"/>
            </div>
            <Button {...buttonProps} clear={true} onClick={handleClose}>
              Cancel
            </Button>
            <Button {...buttonProps} type="submit">
              {decide}
            </Button>
          </form>
        </div>
      </div>;
    }
  };
});
