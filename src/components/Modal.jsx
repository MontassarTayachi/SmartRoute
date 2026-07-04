const Modal = ({ title, children, onClose }) => (
  <div className="modal-backdrop" role="presentation" onClick={onClose}>
    <div
      className="modal-card"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={(event) => event.stopPropagation()}
    >
      <div className="modal-header">
        <h2>{title}</h2>
        <button type="button" className="btn-ghost" onClick={onClose}>
          Fermer
        </button>
      </div>
      <div className="modal-content">{children}</div>
    </div>
  </div>
);

export default Modal;
