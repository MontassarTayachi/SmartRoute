import logo from '../assets/logo.png';

const AppIcon = ({ size = 32, className = '' }) => (
  <img
    src={logo}
    alt="SmartRoute"
    width={size}
    height={size}
    className={className}
  />
);

export default AppIcon;
