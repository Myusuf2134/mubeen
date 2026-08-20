/**
 * Tests for useDisplayWebSocket history management logic (MB-017 waterfall redesign).
 *
 * Note: Testing hook logic in isolation requires extracting the message-handling
 * logic into a pure function. These tests verify the state transition rules:
 * 1. Final messages append to history and truncate to MAX_SIZE
 * 2. Interim messages update a separate state, never enter history
 * 3. When final arrives, interim is cleared
 */

import { describe, it, expect } from 'vitest';

// Extract the history management logic for testing
const HISTORY_MAX_SIZE = 6;

interface RenderPayload {
  text: string;
  source_text: string;
  source: 'scripture' | 'machine';
  machine_generated: boolean;
}

interface BroadcastMessage {
  is_partial: boolean;
  render_payload: RenderPayload | null;
}

/**
 * Pure function to update history based on a new message.
 * This is extracted from the hook's handleMessage callback for testing.
 */
function updateHistoryFromMessage(
  currentHistory: RenderPayload[],
  message: BroadcastMessage
): {
  newHistory: RenderPayload[];
  newInterim: RenderPayload | null;
} {
  const payload = message.render_payload;

  if (message.is_partial) {
    // Interim: update separate state, don't add to history
    return {
      newHistory: currentHistory,
      newInterim: payload,
    };
  } else {
    // Final: add to history, clear interim
    if (payload) {
      const newHistory = [...currentHistory, payload];
      if (newHistory.length > HISTORY_MAX_SIZE) {
        newHistory.shift();  // Remove oldest
      }
      return {
        newHistory,
        newInterim: null,
      };
    }
    return {
      newHistory: currentHistory,
      newInterim: null,
    };
  }
}

describe('useDisplayWebSocket history management', () => {
  it('appends final messages to history', () => {
    const history: RenderPayload[] = [];
    const msg: BroadcastMessage = {
      is_partial: false,
      render_payload: {
        text: 'بسم الله',
        source_text: 'بسم الله',
        source: 'scripture',
        machine_generated: false,
      },
    };

    const { newHistory } = updateHistoryFromMessage(history, msg);

    expect(newHistory).toHaveLength(1);
    expect(newHistory[0].text).toBe('بسم الله');
  });

  it('keeps multiple final messages in order', () => {
    let history: RenderPayload[] = [];

    const messages = [
      { text: 'الحمد لله', source: 'scripture' as const },
      { text: 'رب العالمين', source: 'machine' as const },
      { text: 'الرحمن الرحيم', source: 'scripture' as const },
    ];

    messages.forEach((text) => {
      const msg: BroadcastMessage = {
        is_partial: false,
        render_payload: {
          text: text.text,
          source_text: text.text,
          source: text.source,
          machine_generated: text.source === 'machine',
        },
      };
      const result = updateHistoryFromMessage(history, msg);
      history = result.newHistory;
    });

    expect(history).toHaveLength(3);
    expect(history[0].text).toBe('الحمد لله');
    expect(history[1].text).toBe('رب العالمين');
    expect(history[2].text).toBe('الرحمن الرحيم');
  });

  it('truncates history when exceeding MAX_SIZE', () => {
    let history: RenderPayload[] = [];

    // Add HISTORY_MAX_SIZE + 3 messages
    for (let i = 0; i < HISTORY_MAX_SIZE + 3; i++) {
      const msg: BroadcastMessage = {
        is_partial: false,
        render_payload: {
          text: `Message ${i}`,
          source_text: `Message ${i}`,
          source: 'machine',
          machine_generated: true,
        },
      };
      const result = updateHistoryFromMessage(history, msg);
      history = result.newHistory;
    }

    // Should keep only the last HISTORY_MAX_SIZE
    expect(history).toHaveLength(HISTORY_MAX_SIZE);
    // Oldest messages (0, 1, 2) should be gone
    expect(history[0].text).toBe('Message 3');
    // Newest should be the last one added
    expect(history[HISTORY_MAX_SIZE - 1].text).toBe(`Message ${HISTORY_MAX_SIZE + 2}`);
  });

  it('never adds interim messages to history', () => {
    const history: RenderPayload[] = [];

    const interimMsg: BroadcastMessage = {
      is_partial: true,
      render_payload: {
        text: 'forming text...',
        source_text: 'forming text...',
        source: 'machine',
        machine_generated: false,
      },
    };

    const { newHistory, newInterim } = updateHistoryFromMessage(history, interimMsg);

    expect(newHistory).toHaveLength(0);  // History unchanged
    expect(newInterim).not.toBeNull();   // Interim updated
    expect(newInterim?.text).toBe('forming text...');
  });

  it('updates interim in place without pushing to history', () => {
    const history: RenderPayload[] = [];
    let interim: RenderPayload | null = null;

    // First interim
    const msg1: BroadcastMessage = {
      is_partial: true,
      render_payload: {
        text: 'بسم',
        source_text: 'بسم',
        source: 'machine',
        machine_generated: false,
      },
    };

    let result = updateHistoryFromMessage(history, msg1);
    interim = result.newInterim;
    expect(interim?.text).toBe('بسم');

    // Second interim (should replace, not append)
    const msg2: BroadcastMessage = {
      is_partial: true,
      render_payload: {
        text: 'بسم الله',
        source_text: 'بسم الله',
        source: 'machine',
        machine_generated: false,
      },
    };

    result = updateHistoryFromMessage(result.newHistory, msg2);
    interim = result.newInterim;
    expect(interim?.text).toBe('بسم الله');
    expect(result.newHistory).toHaveLength(0);  // History still empty
  });

  it('clears interim when final message arrives', () => {
    let history: RenderPayload[] = [];
    let interim: RenderPayload | null = null;

    // Set up interim state
    const interimMsg: BroadcastMessage = {
      is_partial: true,
      render_payload: {
        text: 'forming...',
        source_text: 'forming...',
        source: 'machine',
        machine_generated: false,
      },
    };

    let result = updateHistoryFromMessage(history, interimMsg);
    interim = result.newInterim;
    history = result.newHistory;
    expect(interim).not.toBeNull();

    // Final message arrives
    const finalMsg: BroadcastMessage = {
      is_partial: false,
      render_payload: {
        text: 'complete',
        source_text: 'complete',
        source: 'scripture',
        machine_generated: false,
      },
    };

    result = updateHistoryFromMessage(history, finalMsg);
    interim = result.newInterim;
    history = result.newHistory;

    expect(interim).toBeNull();  // Interim cleared
    expect(history).toHaveLength(1);  // Final added to history
    expect(history[0].text).toBe('complete');
  });

  it('handles null payload in final message gracefully', () => {
    const history: RenderPayload[] = [];

    const msg: BroadcastMessage = {
      is_partial: false,
      render_payload: null,
    };

    const { newHistory, newInterim } = updateHistoryFromMessage(history, msg);

    expect(newHistory).toHaveLength(0);  // No payload, not added
    expect(newInterim).toBeNull();
  });
});
