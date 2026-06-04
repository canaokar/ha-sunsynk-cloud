import { css } from "lit";

export const cardStyles = css`
  :host {
    --primary-color: #4fc3f7;
    --success-color: #66bb6a;
    --warning-color: #ffa726;
    --error-color: #ef5350;
    --card-bg: var(--ha-card-background, #fff);
    --text-primary: var(--primary-text-color, #212121);
    --text-secondary: var(--secondary-text-color, #727272);
    --divider: var(--divider-color, #e0e0e0);
  }

  ha-card {
    padding: 16px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .header .title {
    font-size: 18px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .header .status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--success-color);
  }

  .status-dot.offline {
    background: var(--error-color);
  }

  .power-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }

  .power-tile {
    text-align: center;
    padding: 12px 8px;
    border-radius: 8px;
    background: var(--card-bg);
    border: 1px solid var(--divider);
  }

  .power-tile .value {
    font-size: 20px;
    font-weight: 600;
  }

  .power-tile .label {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  .section {
    border-top: 1px solid var(--divider);
    padding-top: 12px;
    margin-top: 12px;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    user-select: none;
    padding: 4px 0;
  }

  .section-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
  }

  .section-content {
    padding-top: 12px;
  }

  .setting-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
  }

  .setting-row .label {
    font-size: 14px;
    color: var(--text-primary);
  }

  .timeline-bar {
    position: relative;
    height: 48px;
    background: var(--divider);
    border-radius: 6px;
    overflow: hidden;
    margin: 12px 0;
  }

  .timeline-slot {
    position: absolute;
    top: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    color: white;
    cursor: pointer;
    transition: opacity 0.2s;
    border-right: 1px solid rgba(255, 255, 255, 0.3);
  }

  .timeline-slot:hover {
    opacity: 0.85;
  }

  .timeline-slot.grid-charge {
    background: #1e88e5;
  }

  .timeline-slot.solar {
    background: #43a047;
  }

  .timeline-slot.disabled {
    background: #9e9e9e;
  }

  .timeline-labels {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: var(--text-secondary);
    padding: 0 2px;
  }

  .day-row {
    display: flex;
    gap: 6px;
    margin: 8px 0;
  }

  .day-toggle {
    width: 36px;
    height: 28px;
    border-radius: 4px;
    border: 1px solid var(--divider);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    cursor: pointer;
    user-select: none;
  }

  .day-toggle.active {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
  }

  .save-bar {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
    margin-top: 12px;
  }

  .soc-badge {
    font-size: 24px;
    font-weight: 700;
  }
`;
