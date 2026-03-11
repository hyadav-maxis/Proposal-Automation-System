import { NavLink } from 'react-router-dom';

export default function Layout({ children }) {
  return (
    <>
      <header className="topbar">
        <NavLink to="/" className="topbar-brand">
          <div className="brand-icon">🚀</div>
          Proposal Automation System
        </NavLink>
        <nav className="topbar-nav">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
            New Proposal
          </NavLink>
          <NavLink to="/pricing-config" className={({ isActive }) => isActive ? 'active' : ''}>
            ⚙️ Pricing
          </NavLink>
          <NavLink to="/chat" className={({ isActive }) => isActive ? 'active' : ''}>
            🤖 AI Assistant
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => isActive ? 'active' : ''}>
            ⚙️ Settings
          </NavLink>
          <NavLink to="/proposals" className={({ isActive }) => isActive ? 'active' : ''}>
            📋 All Proposals
          </NavLink>
        </nav>
      </header>
      <main>{children}</main>
    </>
  );
}
