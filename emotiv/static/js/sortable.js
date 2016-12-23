/* global define */

// Sortable implementation taken from React DnD examples, with some modification.
//
// https://github.com/gaearon/react-dnd/tree/master/examples/04%20Sortable/Simple

define([
  'react',
  'react-dnd',
  'react-dnd-html5-backend',
  'reactDOM'
], (React, ReactDnD, HTML5Backend, ReactDOM) => {
  const {Children, Component} = React;
  const {DragDropContext, DragSource, DropTarget} = ReactDnD;
  const {findDOMNode} = ReactDOM;

  @DragDropContext(HTML5Backend)
  class SortableContainer extends Component {
    render() {
      const {children, moveCard, enabled, ...props} = this.props;
      if (!enabled) {
        return <div {...props}>{children}</div>;
      }
      return (
        <div {...props}>
          {Children.map(children, (child, i) => (
            <Card key={child.key} index={i} id={child.key} moveCard={moveCard}>
              {child}
            </Card>)
          )}
        </div>
      );
    }
  }

  const cardSource = {
    beginDrag(props) {
      return {
        id: props.id,
        index: props.index
      };
    }
  };

  const cardTarget = {
    hover(props, monitor, component) {
      const dragIndex = monitor.getItem().index;
      const hoverIndex = props.index;

      // Don't replace items with themselves
      if (dragIndex === hoverIndex) {
        return;
      }

      // Determine rectangle on screen
      const hoverBoundingRect = findDOMNode(component).getBoundingClientRect();

      // Get vertical middle
      const hoverMiddleY =
        (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;

      // Determine mouse position
      const clientOffset = monitor.getClientOffset();

      // Get pixels to the top
      const hoverClientY = clientOffset.y - hoverBoundingRect.top;

      // Only perform the move when the mouse has crossed half of the items height
      // When dragging downwards, only move when the cursor is below 50%
      // When dragging upwards, only move when the cursor is above 50%

      // Dragging downwards
      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
        return;
      }

      // Dragging upwards
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
        return;
      }

      // Time to actually perform the action
      props.moveCard(dragIndex, hoverIndex);

      // Note: we're mutating the monitor item here!
      // Generally it's better to avoid mutations,
      // but it's good here for the sake of performance
      // to avoid expensive index searches.
      monitor.getItem().index = hoverIndex;
    }
  };

  @DropTarget('card', cardTarget, connect => ({
    connectDropTarget: connect.dropTarget()
  }))
  @DragSource('card', cardSource, (connect, monitor) => ({
    connectDragSource: connect.dragSource(),
    isDragging: monitor.isDragging()
  }))
  class Card extends Component {
    render() {
      const {
        children, isDragging, connectDragSource, connectDropTarget
      } = this.props;
      const opacity = isDragging ? 0 : 1;

      return connectDragSource(connectDropTarget(
        <div style={{
          // Workaround for a Chrome bug.
          // See https://bugs.chromium.org/p/chromium/issues/detail?id=605119
          // and https://github.com/gaearon/react-dnd/issues/454
          transform: 'translate3d(0,0,0)',

          opacity
        }}>
          {children}
        </div>
      ));
    }
  }

  return {SortableContainer};
});
