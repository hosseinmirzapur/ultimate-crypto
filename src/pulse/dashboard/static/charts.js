"""Minimal inline candlestick chart — no external dependencies."""

class MiniChart {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;
    this.canvas = document.createElement('canvas');
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
    this.data = [];
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.container.getBoundingClientRect();
    this.canvas.width = rect.width || 400;
    this.canvas.height = 300;
    this.draw();
  }

  setData(data) {
    this.data = data.slice(-100);
    this.draw();
  }

  draw() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    ctx.fillStyle = '#111827';
    ctx.fillRect(0, 0, w, h);

    if (this.data.length < 2) {
      ctx.fillStyle = '#5a6178';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Waiting for data...', w / 2, h / 2);
      return;
    }

    const prices = this.data.flatMap(d => [d.high, d.low]);
    const minP = Math.min(...prices);
    const maxP = Math.max(...prices);
    const range = maxP - minP || 1;
    const candleW = (w / this.data.length) * 0.7;
    const gap = (w / this.data.length) * 0.3;

    ctx.strokeStyle = '#1a2235';
    ctx.lineWidth = 1;
    for (let i = 1; i < 5; i++) {
      const y = (h / 5) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    this.data.forEach((c, i) => {
      const x = i * (candleW + gap) + candleW / 2;
      const isUp = c.close >= c.open;
      const color = isUp ? '#00d4aa' : '#ff4d4d';

      const highY = h - ((c.high - minP) / range) * (h - 40) - 20;
      const lowY = h - ((c.low - minP) / range) * (h - 40) - 20;
      const openY = h - ((c.open - minP) / range) * (h - 40) - 20;
      const closeY = h - ((c.close - minP) / range) * (h - 40) - 20;

      ctx.strokeStyle = color;
      ctx.beginPath();
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
      ctx.stroke();

      const bodyTop = Math.min(openY, closeY);
      const bodyH = Math.max(Math.abs(closeY - openY), 1);
      ctx.fillStyle = color;
      ctx.fillRect(x - candleW / 2, bodyTop, candleW, bodyH);
    });

    ctx.fillStyle = '#8b92a8';
    ctx.font = '11px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`${maxP.toFixed(2)}`, 4, 16);
    ctx.fillText(`${minP.toFixed(2)}`, 4, h - 8);
  }
}

window.MiniChart = MiniChart;
