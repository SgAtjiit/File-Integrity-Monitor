import React, { useState, useEffect } from 'react';
import { Shield, Activity, FileText, AlertTriangle, CheckCircle, RefreshCw, FolderPlus, Trash2, Terminal, Lock, Unlock, Folder } from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import * as api from './api';

function App() {
  const [status, setStatus] = useState(null);
  const [directories, setDirectories] = useState([]);
  const [logs, setLogs] = useState([]);
  const [integrityResult, setIntegrityResult] = useState(null);
  const [newDir, setNewDir] = useState('');
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [chartData, setChartData] = useState([]);
  const [scanHistory, setScanHistory] = useState([]);
  const [selectedScan, setSelectedScan] = useState(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportShift, setExportShift] = useState(3);

  // Decrypt Tool State
  const [showDecryptModal, setShowDecryptModal] = useState(false);
  const [decryptInput, setDecryptInput] = useState("");
  const [decryptShift, setDecryptShift] = useState(3);
  const [decryptResult, setDecryptResult] = useState("");

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    const statusData = await api.getStatus();
    setStatus(statusData);

    const dirsData = await api.getDirectories();
    if (dirsData.directories) setDirectories(dirsData.directories);

    // Load chart data from localStorage
    const history = JSON.parse(localStorage.getItem('fim_scan_history') || '[]');
    setScanHistory(history.reverse()); // Newest first

    // Format for chart (take last 10 entries)
    const formattedData = history.slice(-10).reverse().map(entry => ({
      name: new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      events: entry.events ? entry.events.length : (entry.eventCount || 0) // Handle legacy format
    }));
    setChartData(formattedData);
  };

  const handleAddDir = async (e) => {
    e.preventDefault();
    if (!newDir) return;
    setLoading(true);
    const res = await api.addDirectory(newDir.trim());

    if (res.error) {
      alert(res.error);
      if (res.details) {
        alert("Details:\n" + res.details.join("\n"));
      }
    } else {
      setDirectories(res.directories);
      setNewDir('');
      if (res.errors && res.errors.length > 0) {
        alert("Some directories could not be added:\n" + res.errors.join("\n"));
      }
    }
    setLoading(false);
  };

  const handleRemoveDir = async (path) => {
    if (!window.confirm(`Stop monitoring ${path}?`)) return;
    const res = await api.removeDirectory(path);
    if (res.directories) setDirectories(res.directories);
  };

  const handleCheckIntegrity = async () => {
    setChecking(true);
    const res = await api.checkIntegrity();
    setIntegrityResult(res);
    setChecking(false);
    setLogs(res.scan_logs || []);

    // Save to localStorage
    const history = JSON.parse(localStorage.getItem('fim_scan_history') || '[]');

    // Store full scan result
    const scanRecord = {
      timestamp: new Date().toISOString(),
      status: res.status,
      events: res.events || [],
      scan_logs: res.scan_logs || []
    };

    history.push(scanRecord);
    localStorage.setItem('fim_scan_history', JSON.stringify(history));

    fetchData();
  };

  const handleExportLogs = async () => {
    if (logs.length === 0) {
      alert("No logs to export.");
      return;
    }

    try {
      const res = await api.exportLogs(logs, exportShift);
      if (res.encrypted_logs) {
        // Create blob and download
        const blob = new Blob([res.encrypted_logs], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = res.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setShowExportModal(false);
      }
    } catch (err) {
      alert("Failed to export logs");
    }
  };

  const handleDecrypt = async () => {
    if (!decryptInput) return;
    try {
      const res = await api.decryptText(decryptInput, decryptShift);
      if (res.decrypted_text) {
        setDecryptResult(res.decrypted_text);
      }
    } catch (err) {
      alert("Decryption failed");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 text-gray-300 selection:bg-cyan-400 selection:text-black overflow-x-hidden">
      <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-8">

        {/* ✅ HEADER */}
        <header className="flex flex-col md:flex-row items-center justify-between py-6 border-b border-white/5 gap-4">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center space-x-4"
          >
            <motion.div whileHover={{ scale: 1.05 }} className="relative">
              <div className="absolute inset-0 bg-cyan-500/20 blur-xl rounded-xl"></div>
              <div className="relative p-3 rounded-xl border border-cyan-400/30 hover:border-cyan-400/60 backdrop-blur-md bg-white/5 transition-all shadow-lg">
                <Shield className="w-8 h-8 text-cyan-400" />
              </div>
            </motion.div>
            <div>
              <h1 className="text-4xl font-bold text-white tracking-tight drop-shadow-lg">
                FIM<span className="text-cyan-400">.Core</span>
              </h1>
              <p className="text-xs font-mono text-gray-500 uppercase tracking-widest mt-1">
                File Integrity Monitor
              </p>
            </div>
          </motion.div>

          {/* ✅ STATUS BADGE */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center space-x-3 px-5 py-3 rounded-full border border-green-400/20 hover:border-green-400/40 backdrop-blur-md bg-white/5 transition-all"
          >
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className={`w-2.5 h-2.5 rounded-full ${status?.status === 'running'
                ? 'bg-green-400 shadow-lg shadow-green-400/50'
                : 'bg-red-500 shadow-lg shadow-red-500/50'
                }`}
            />
            <span className="text-sm font-mono text-gray-300">
              {status?.status === 'running' ? 'ONLINE' : 'OFFLINE'}
            </span>
          </motion.div>
        </header>

        {/* ✅ STATS GRID */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatsCard
            title="Monitored Targets"
            value={directories.length}
            icon={Folder}
            color="from-cyan-500/20 to-cyan-400/10"
            borderColor="border-cyan-400/30"
            textColor="text-cyan-400"
            delay={0.1}
          />
          <StatsCard
            title="Total Events"
            value={logs.length}
            icon={Activity}
            color="from-purple-500/20 to-purple-400/10"
            borderColor="border-purple-400/30"
            textColor="text-purple-400"
            delay={0.2}
          />
          <StatsCard
            title="Security Status"
            value="SECURE"
            icon={Lock}
            color="from-green-500/20 to-green-400/10"
            borderColor="border-green-400/30"
            textColor="text-green-400"
            delay={0.3}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* ✅ MAIN CONTENT */}
          <div className="lg:col-span-2 space-y-8">

            {/* ✅ DIRECTORY MANAGEMENT */}
            <div className="rounded-2xl border border-cyan-400/20 bg-white/5 p-6 mb-8">
              <h2 className="text-lg font-semibold text-white mb-4">Target Directories</h2>

              <form onSubmit={handleAddDir} className="flex gap-3 mb-4">
                <input
                  type="text"
                  value={newDir}
                  onChange={(e) => setNewDir(e.target.value)}
                  placeholder="Enter absolute paths (comma separated)..."
                  className="w-full px-4 py-2 rounded bg-slate-800 border border-cyan-400/20 text-gray-100"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded bg-cyan-500 text-white font-semibold hover:bg-cyan-400 disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add'}
                </button>
              </form>

              <ul className="space-y-2">
                {directories.map((dir) => (
                  <li key={dir} className="flex items-center justify-between bg-slate-800 px-4 py-2 rounded">
                    <span className="text-gray-300 font-mono">{dir}</span>
                    <button
                      onClick={() => handleRemoveDir(dir)}
                      className="text-red-400 hover:text-red-600"
                    >
                      Remove
                    </button>
                  </li>
                ))}
                {directories.length === 0 && (
                  <li className="text-gray-500 italic">No monitored directories.</li>
                )}
              </ul>
            </div>

            {/* ✅ SCAN BUTTON */}
            <div className="flex justify-center">
              <button
                onClick={handleCheckIntegrity}
                disabled={checking || directories.length === 0}
                className="px-6 py-3 rounded bg-green-500 text-white font-semibold hover:bg-green-400 disabled:opacity-50 transition"
              >
                {checking ? 'Scanning...' : 'Run Integrity Scan'}
              </button>
            </div>

            {/* ✅ SCAN RESULTS */}
            {integrityResult && (
              <div className="rounded-2xl border border-green-400/20 bg-white/5 p-6">
                <h3 className="text-lg font-semibold text-green-400 mb-2">
                  {integrityResult.status === 'clean' ? 'No Changes Detected' : 'Integrity Issues Found'}
                </h3>
                <p className="text-gray-400 mb-4">{integrityResult.message}</p>

                {integrityResult.events && integrityResult.events.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-xs font-mono border-collapse">
                      <thead>
                        <tr className="bg-slate-900/60 text-gray-400">
                          <th className="p-2 text-left">Type</th>
                          <th className="p-2 text-left">File Path</th>
                          <th className="p-2 text-left">Before (Baseline)</th>
                          <th className="p-2 text-left">After (Current)</th>
                          <th className="p-2 text-left">Message</th>
                        </tr>
                      </thead>
                      <tbody>
                        {integrityResult.events.map((event, idx) => (
                          <tr key={idx} className="border-b border-white/5 hover:bg-slate-800/40 transition-all">
                            <td className="p-2">
                              <span className={`font-bold px-2 py-1 rounded-full tracking-wider whitespace-nowrap ${event.type === 'MODIFIED'
                                ? 'bg-yellow-500/20 text-yellow-400'
                                : event.type === 'DELETED'
                                  ? 'bg-red-500/20 text-red-400'
                                  : event.type === 'ADDED'
                                    ? 'bg-blue-500/20 text-blue-400'
                                    : 'bg-green-500/20 text-green-400'
                                }`}>
                                {event.type}
                              </span>
                            </td>
                            <td className="p-2 break-all text-gray-300">{event.path}</td>
                            <td className="p-2 break-all text-gray-500">
                              {event.baseline_checksum || <span className="italic text-gray-600">N/A</span>}
                            </td>
                            <td className="p-2 break-all text-gray-500">
                              {event.current_checksum || <span className="italic text-gray-600">N/A</span>}
                            </td>
                            <td className="p-2 text-gray-400">{event.message}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ✅ SIDEBAR */}
          <div className="space-y-8">

            {/* ✅ CHART (UPDATED) */}
            <div className="rounded-2xl px-6 py-4 border border-purple-400/20 bg-white/5 backdrop-blur-lg">
              <h3 className="text-sm font-semibold text-purple-400 mb-4 uppercase tracking-wide">
                Event Activity
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} stroke="#94a3b8" />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#ffffff', fontSize: 12, fontWeight: 'bold' }}
                    tickLine={{ stroke: '#cbd5e1' }}
                    axisLine={{ stroke: '#cbd5e1' }}
                  />
                  <YAxis
                    allowDecimals={false} // Prevents 0.25, 0.5, etc.
                    tick={{ fill: '#ffffff', fontSize: 12, fontWeight: 'bold' }}
                    tickLine={{ stroke: '#cbd5e1' }}
                    axisLine={{ stroke: '#cbd5e1' }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#e2e8f0' }}
                    labelStyle={{ color: '#94a3b8' }}
                  />
                  <Area type="monotone" dataKey="events" fill="purple" stroke="#d8b4fe" strokeWidth={2} fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* ✅ LOGS TERMINAL */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 }}
              className="rounded-2xl overflow-hidden flex flex-col h-[500px] border border-white/10 hover:border-white/20 transition-all backdrop-blur-md bg-white/5 shadow-lg"
            >
              <div className="p-4 border-b border-white/5 bg-slate-800/30 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-400 flex items-center space-x-2 uppercase tracking-wider">
                  <Terminal className="w-4 h-4 text-gray-500" />
                  <span>System Logs</span>
                </h3>
                <button
                  onClick={() => setShowExportModal(true)}
                  className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-cyan-400 transition-colors"
                >
                  Export Encrypted
                </button>
                <button
                  onClick={() => setShowDecryptModal(true)}
                  className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-green-400 transition-colors ml-2"
                >
                  Decrypt Tool
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-xs bg-slate-900/30 scrollbar-thin scrollbar-thumb-cyan-700/40 scrollbar-track-transparent">
                {logs.length > 0 ? (
                  logs.map((log, idx) => (
                    <div
                      key={idx}
                      className="text-gray-400 border-b border-white/5 pb-1 last:border-0 hover:text-gray-300 transition-colors group"
                    >
                      <span className="text-gray-600 mr-3 group-hover:text-gray-500 transition-colors">
                        [{new Date().toLocaleTimeString()}]
                      </span>
                      <span>{log}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-gray-700 py-4 italic">
                    -- No scan logs yet --
                  </div>
                )}
              </div>
            </motion.div>

            {/* ✅ SCAN HISTORY */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <h3 className="text-sm font-semibold text-gray-400 mb-4 uppercase tracking-wide">
                Recent Scans
              </h3>
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-700">
                {scanHistory.map((scan, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      setIntegrityResult(scan);
                      setLogs(scan.scan_logs || []);
                      setSelectedScan(idx);
                    }}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedScan === idx
                      ? 'bg-cyan-500/20 border-cyan-500/50'
                      : 'bg-slate-800/50 border-white/5 hover:bg-slate-800 hover:border-white/10'
                      }`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-mono text-gray-400">
                        {new Date(scan.timestamp).toLocaleString()}
                      </span>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${scan.status === 'clean'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                        }`}>
                        {scan.status === 'clean' ? 'CLEAN' : 'CHANGED'}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {scan.events ? scan.events.length : (scan.eventCount || 0)} events detected
                    </div>
                  </div>
                ))}
                {scanHistory.length === 0 && (
                  <div className="text-center text-gray-600 text-sm py-4">No history available</div>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* ✅ EXPORT MODAL */}
      <AnimatePresence>
        {showExportModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-slate-900 border border-cyan-500/30 p-6 rounded-2xl w-full max-w-md shadow-2xl"
            >
              <h3 className="text-xl font-bold text-white mb-4">Export Encrypted Logs</h3>
              <p className="text-gray-400 text-sm mb-4">
                Enter a Caesar Cipher shift value (key) to encrypt your logs before downloading.
              </p>

              <div className="mb-6">
                <label className="block text-xs font-mono text-cyan-400 mb-2">ENCRYPTION KEY (SHIFT)</label>
                <input
                  type="number"
                  value={exportShift}
                  onChange={(e) => setExportShift(e.target.value)}
                  className="w-full bg-slate-800 border border-white/10 rounded px-4 py-2 text-white focus:border-cyan-500 outline-none"
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowExportModal(false)}
                  className="px-4 py-2 rounded text-gray-400 hover:text-white hover:bg-white/5 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleExportLogs}
                  className="px-4 py-2 rounded bg-cyan-500 text-white font-semibold hover:bg-cyan-400 transition"
                >
                  Download
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ✅ DECRYPT MODAL */}
      <AnimatePresence>
        {showDecryptModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-slate-900 border border-green-500/30 p-6 rounded-2xl w-full max-w-2xl shadow-2xl"
            >
              <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                <Unlock className="w-5 h-5 mr-2 text-green-400" />
                Decryption Tool
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-mono text-gray-400 mb-2">ENCRYPTED TEXT</label>
                  <textarea
                    value={decryptInput}
                    onChange={(e) => setDecryptInput(e.target.value)}
                    className="w-full h-40 bg-slate-800 border border-white/10 rounded p-3 text-xs font-mono text-gray-300 focus:border-green-500 outline-none resize-none"
                    placeholder="Paste encrypted logs here..."
                  />
                  <div className="mt-4">
                    <label className="block text-xs font-mono text-green-400 mb-2">DECRYPTION KEY (SHIFT)</label>
                    <input
                      type="number"
                      value={decryptShift}
                      onChange={(e) => setDecryptShift(e.target.value)}
                      className="w-full bg-slate-800 border border-white/10 rounded px-4 py-2 text-white focus:border-green-500 outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-gray-400 mb-2">DECRYPTED RESULT</label>
                  <div className="w-full h-64 bg-black/40 border border-white/5 rounded p-3 text-xs font-mono text-green-400 overflow-y-auto whitespace-pre-wrap">
                    {decryptResult || "Result will appear here..."}
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowDecryptModal(false)}
                  className="px-4 py-2 rounded text-gray-400 hover:text-white hover:bg-white/5 transition"
                >
                  Close
                </button>
                <button
                  onClick={handleDecrypt}
                  className="px-4 py-2 rounded bg-green-600 text-white font-semibold hover:bg-green-500 transition shadow-lg shadow-green-900/20"
                >
                  Decrypt
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function StatsCard({ title, value, icon: Icon, color, borderColor, textColor, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ scale: 1.03, translateY: -5 }}
      className={`p-6 rounded-2xl relative overflow-hidden group border ${borderColor} hover:${borderColor} transition-all cursor-pointer backdrop-blur-md bg-white/5 shadow-lg`}
    >
      <div className={`absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity duration-300 ${color}`}>
        <Icon className="w-32 h-32 transform rotate-12 translate-x-8 -translate-y-8" />
      </div>
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-gray-500 font-medium text-sm uppercase tracking-widest">{title}</h3>
          <div className={`p-2.5 rounded-lg bg-gradient-to-br ${color} ${textColor}`}>
            <Icon className="w-5 h-5" />
          </div>
        </div>
        <p className="text-5xl font-bold text-white tracking-tight">{value}</p>
      </div>
      <div className={`absolute inset-0 bg-gradient-to-r ${color} opacity-0 group-hover:opacity-5 transition-opacity rounded-2xl`}></div>
    </motion.div>
  );
}

export default App;