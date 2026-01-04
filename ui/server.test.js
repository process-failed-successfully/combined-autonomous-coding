const request = require('supertest');
const app = require('./server');

describe('POST /api/agents/:id/heartbeat', () => {
  it('should add logs to the agent state', async () => {
    const agentId = 'test-agent';
    const logs = ['log entry 1', 'log entry 2'];

    await request(app)
      .post(`/api/agents/${agentId}/heartbeat`)
      .send({ logs })
      .expect(200);

    const response = await request(app).get('/api/ui/agents');
    const agent = response.body.agents.find(a => a.id === agentId);
    expect(agent.state.logs).toEqual(logs);
  });

  it('should truncate logs to the last 50 entries', async () => {
    const agentId = 'test-agent-2';
    const logs = Array.from({ length: 100 }, (_, i) => `log entry ${i}`);

    await request(app)
      .post(`/api/agents/${agentId}/heartbeat`)
      .send({ logs })
      .expect(200);

    const response = await request(app).get('/api/ui/agents');
    const agent = response.body.agents.find(a => a.id === agentId);
    expect(agent.state.logs.length).toBe(50);
    expect(agent.state.logs[0]).toBe('log entry 50');
  });
});
