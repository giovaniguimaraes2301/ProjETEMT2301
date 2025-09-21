import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import './App.css';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  // Estados principais
  const [activeSection, setActiveSection] = useState('Dashboard');
  const [vitalSigns, setVitalSigns] = useState([]);
  const [latestReadings, setLatestReadings] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [esp32Status, setEsp32Status] = useState({ connected: false, lastReading: null });
  const [esp32Config, setEsp32Config] = useState({
    wifiSSID: '',
    wifiPassword: '',
    deviceName: 'ESP32-VitalTech',
    apiURL: `${API}/esp32/data`
  });
  const [profile, setProfile] = useState({
    nome: 'Visitante da Feira',
    idade: '',
    genero: '',
    altura: '',
    peso: '',
    grupo_sanguineo: '',
    telefone: '',
    email: '',
    endereco: '',
    cartao_saude: '',
    condicoes_medicas: '',
    alergias: '',
    medicacoes: '',
    contatos_emergencia: '',
    informacoes_adicionais: '',
    foto_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [esp32Connected, setEsp32Connected] = useState(false);

  // Buscar dados da API
  const fetchLatestReadings = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/vital-signs/latest`);
      setLatestReadings(response.data);
    } catch (error) {
      console.error('Erro ao buscar últimas leituras:', error);
    }
  }, []);

  const fetchVitalSigns = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/vital-signs?limit=50&hours=24`);
      setVitalSigns(response.data.vital_signs || []);
    } catch (error) {
      console.error('Erro ao buscar sinais vitais:', error);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/alerts?limit=20`);
      setAlerts(response.data.alerts || []);
    } catch (error) {
      console.error('Erro ao buscar alertas:', error);
    }
  }, []);

  const fetchProfile = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/profile`);
      setProfile(prevProfile => ({ ...prevProfile, ...response.data }));
    } catch (error) {
      console.error('Erro ao buscar perfil:', error);
    }
  }, []);

  // Salvar perfil
  const saveProfile = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/profile`, profile);
      showToast('Perfil salvo com sucesso!');
    } catch (error) {
      console.error('Erro ao salvar perfil:', error);
      showToast('Erro ao salvar perfil', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Executar análise IA
  const runAIAnalysis = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/analysis/run`);
      showToast(`Análise IA executada: ${response.data.health_status}`);
      await fetchAlerts(); // Atualizar alertas
    } catch (error) {
      console.error('Erro na análise IA:', error);
      showToast('Erro na análise IA', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Gerar relatório PDF
  const generatePDFReport = async (period = 'daily') => {
    try {
      setLoading(true);
      console.log(`Gerando relatório ${period}...`);
      
      const response = await axios.get(`${API}/reports/data/${period}`);
      const data = response.data;
      
      console.log('Dados do relatório:', data);

      // Importar jsPDF e autoTable dinamicamente
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF('p', 'pt', 'a4');
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();

      // Header com cor azul
      doc.setFillColor(48, 102, 211);
      doc.rect(0, 0, pageWidth, 60, 'F');
      
      // Logo VT
      doc.setFillColor(255, 255, 255);
      doc.rect(20, 15, 30, 30, 'F');
      doc.setFontSize(16);
      doc.setTextColor(48, 102, 211);
      doc.text('VT', 28, 35);
      
      // Título
      doc.setFontSize(18);
      doc.setTextColor(255, 255, 255);
      doc.setFont('helvetica', 'bold');
      doc.text('VitalTech - Relatório Médico', 60, 35);

      // Data de geração
      doc.setFontSize(10);
      doc.text(`Gerado: ${new Date().toLocaleString('pt-BR')}`, pageWidth - 150, 25);

      // Informações do paciente
      doc.setFontSize(12);
      doc.setTextColor(0, 0, 0);
      doc.setFont('helvetica', 'normal');
      
      const patientName = data.patient_profile?.nome || 'Visitante da Feira';
      const patientAge = data.patient_profile?.idade || 'N/A';
      
      doc.text(`Paciente: ${patientName}`, 20, 90);
      doc.text(`Idade: ${patientAge} anos`, 20, 110);
      doc.text(`Período: ${period === 'daily' ? 'Diário' : period === 'weekly' ? 'Semanal' : 'Mensal'}`, 20, 130);
      doc.text(`Total de leituras: ${data.vital_signs?.length || 0}`, 20, 150);

      let currentY = 180;

      // Resumo dos sinais vitais
      if (data.vital_signs && data.vital_signs.length > 0) {
        doc.setFontSize(14);
        doc.setFont('helvetica', 'bold');
        doc.text('Resumo dos Sinais Vitais:', 20, currentY);
        currentY += 25;

        // Calcular estatísticas
        const stats = {};
        data.vital_signs.forEach(reading => {
          const type = reading.sensor_type;
          if (!stats[type]) {
            stats[type] = { values: [], unit: reading.unit || '' };
          }
          stats[type].values.push(reading.value);
        });

        // Mostrar estatísticas
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        
        Object.keys(stats).forEach(type => {
          const values = stats[type].values;
          const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1);
          const min = Math.min(...values);
          const max = Math.max(...values);
          
          const typeName = type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
          doc.text(`${typeName}: Média ${avg}${stats[type].unit}, Min ${min}, Max ${max}`, 30, currentY);
          currentY += 15;
        });

        currentY += 20;

        // Tabela manual (sem autoTable por enquanto)
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Últimos Registros:', 20, currentY);
        currentY += 20;

        // Cabeçalho da tabela
        doc.setFillColor(48, 102, 211);
        doc.rect(20, currentY, pageWidth - 40, 20, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text('Data/Hora', 25, currentY + 15);
        doc.text('Sensor', 150, currentY + 15);
        doc.text('Valor', 300, currentY + 15);
        doc.text('Unidade', 400, currentY + 15);
        currentY += 25;

        // Dados da tabela
        doc.setTextColor(0, 0, 0);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        
        const recentData = data.vital_signs.slice(0, 12); // Primeiros 12 registros
        recentData.forEach((reading, index) => {
          if (currentY > pageHeight - 50) {
            doc.addPage();
            currentY = 40;
          }
          
          const bgColor = index % 2 === 0 ? [250, 250, 255] : [255, 255, 255];
          doc.setFillColor(...bgColor);
          doc.rect(20, currentY - 10, pageWidth - 40, 15, 'F');
          
          const dateTime = new Date(reading.timestamp).toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          });
          
          const sensorName = reading.sensor_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
          
          doc.text(dateTime, 25, currentY);
          doc.text(sensorName, 150, currentY);
          doc.text(reading.value.toString(), 300, currentY);
          doc.text(reading.unit || '', 400, currentY);
          currentY += 15;
        });

        currentY += 10;
      }

      // Alertas
      if (data.alerts && data.alerts.length > 0) {
        if (currentY > pageHeight - 100) {
          doc.addPage();
          currentY = 40;
        }
        
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(0, 0, 0);
        doc.text('Alertas do Sistema:', 20, currentY);
        currentY += 20;
        
        data.alerts.slice(0, 8).forEach((alert, index) => {
          if (currentY > pageHeight - 40) {
            doc.addPage();
            currentY = 40;
          }
          
          doc.setFontSize(9);
          doc.setFont('helvetica', 'normal');
          doc.text(`• ${alert.title || 'Alerta'}: ${alert.message || 'N/A'}`, 30, currentY);
          currentY += 12;
        });
      } else {
        if (currentY > pageHeight - 60) {
          doc.addPage();
          currentY = 40;
        }
        doc.setFontSize(10);
        doc.setFont('helvetica', 'italic');
        doc.setTextColor(128, 128, 128);
        doc.text('Nenhum alerta registrado no período.', 30, currentY);
      }

      // Footer
      const footerY = pageHeight - 30;
      doc.setFontSize(8);
      doc.setTextColor(128, 128, 128);
      doc.text('Relatório gerado automaticamente pelo VitalTech', 20, footerY);
      doc.text('Página 1', pageWidth - 60, footerY);

      // Salvar o PDF
      const fileName = `VitalTech_Relatorio_${period}_${new Date().toISOString().slice(0,10)}.pdf`;
      doc.save(fileName);
      
      showToast(`Relatório ${period} gerado e baixado com sucesso!`);
      console.log('PDF gerado com sucesso');
      
    } catch (error) {
      console.error('Erro detalhado ao gerar relatório:', error);
      showToast(`Erro ao gerar relatório: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Exportar CSV
  const exportCSV = () => {
    if (vitalSigns.length === 0) {
      showToast('Nenhum dado para exportar', 'warning');
      return;
    }

    const headers = ['Data/Hora', 'Sensor', 'Valor', 'Unidade'];
    const csvContent = [
      headers.join(','),
      ...vitalSigns.map(reading => [
        new Date(reading.timestamp).toLocaleString('pt-BR'),
        reading.sensor_type,
        reading.value,
        reading.unit || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `vitaltech_dados_${new Date().toISOString().slice(0,10)}.csv`;
    link.click();
    showToast('CSV exportado!');
  };

  // Limpar dados de demonstração
  const cleanupDemoData = async () => {
    if (window.confirm('Tem certeza que deseja limpar todos os dados de demonstração?')) {
      try {
        setLoading(true);
        await axios.post(`${API}/data/cleanup`);
        showToast('Dados limpos com sucesso!');
        // Atualizar dados
        await fetchLatestReadings();
        await fetchVitalSigns();
        await fetchAlerts();
      } catch (error) {
        console.error('Erro ao limpar dados:', error);
        showToast('Erro ao limpar dados', 'error');
      } finally {
        setLoading(false);
      }
    }
  };

  // Preencher dados de exemplo
  const fillSampleData = () => {
    setProfile({
      ...profile,
      nome: 'João Silva',
      idade: '45',
      genero: 'Masculino',
      altura: '175',
      peso: '78',
      grupo_sanguineo: 'O+',
      telefone: '(11) 99999-9999',
      email: 'joao.silva@example.com',
      endereco: 'Rua Exemplo, 100',
      condicoes_medicas: 'Hipertensão controlada',
      alergias: 'Nenhuma conhecida',
      medicacoes: 'Losartana 50mg',
      contatos_emergencia: 'Maria Silva - (11) 88888-8888'
    });
  };

  // Verificar status ESP32
  const checkESP32Status = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/esp32/status`);
      setEsp32Connected(response.data.connected);
    } catch (error) {
      console.error('Erro ao verificar ESP32:', error);
      setEsp32Connected(false);
    }
  }, []);

  // Tela cheia
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullscreen(true);
      }).catch(err => {
        console.error('Erro ao entrar em tela cheia:', err);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      }).catch(err => {
        console.error('Erro ao sair da tela cheia:', err);
      });
    }
  };

  // Detectar mudanças de tela cheia
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);
  const showToast = (message, type = 'success') => {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  };

  // Calcular IMC
  const calculateIMC = () => {
    const altura = parseFloat(profile.altura);
    const peso = parseFloat(profile.peso);
    if (altura && peso) {
      const imc = peso / ((altura / 100) ** 2);
      return imc.toFixed(1);
    }
    return '--';
  };

  const getIMCClassification = (imc) => {
    const imcNum = parseFloat(imc);
    if (imcNum < 18.5) return 'Magreza';
    if (imcNum < 25) return 'Normal';
    if (imcNum < 30) return 'Sobrepeso';
    return 'Obesidade';
  };

  // Preparar dados para gráfico
  const prepareChartData = () => {
    // Se não há dados, retornar estrutura vazia
    if (!vitalSigns || vitalSigns.length === 0) {
      console.log('Sem dados para o gráfico');
      return {
        labels: ['Aguardando dados...'],
        datasets: [
          {
            label: 'Freq. Cardíaca (bpm)',
            data: [0],
            borderColor: '#3066d3',
            backgroundColor: 'rgba(48, 102, 211, 0.1)',
            tension: 0.2,
            fill: false,
          },
          {
            label: 'Pressão (mmHg)',
            data: [0],
            borderColor: '#e67e22',
            backgroundColor: 'rgba(230, 126, 34, 0.1)',
            tension: 0.2,
            fill: false,
          },
          {
            label: 'Oxigenação (%)',
            data: [0],
            borderColor: '#27ae60',
            backgroundColor: 'rgba(39, 174, 96, 0.1)',
            tension: 0.2,
            fill: false,
          },
          {
            label: 'Temperatura (°C)',
            data: [0],
            borderColor: '#c0392b',
            backgroundColor: 'rgba(192, 57, 43, 0.1)',
            tension: 0.2,
            fill: false,
          },
          {
            label: 'GSR (Ω)',
            data: [0],
            borderColor: '#8e44ad',
            backgroundColor: 'rgba(142, 68, 173, 0.1)',
            tension: 0.2,
            fill: false,
            yAxisID: 'y1',
          },
        ]
      };
    }

    // Debug: Log dos dados recebidos
    console.log('Dados vitais recebidos:', vitalSigns.slice(0, 5));

    // Preparar dados organizados por sensor
    const sensorData = {
      heart_rate: [],
      blood_pressure: [],
      oxygen_saturation: [],
      temperature: [],
      gsr: []
    };
    
    const timeLabels = [];
    
    // Agrupar dados por timestamp (pegar os últimos 15 pontos)
    const recentReadings = vitalSigns.slice(0, 30); // Mais dados para garantir cobertura
    
    // Criar um mapa de timestamps únicos
    const timestampMap = new Map();
    
    recentReadings.forEach(reading => {
      const timestamp = reading.timestamp;
      const timeLabel = new Date(timestamp).toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      });
      
      if (!timestampMap.has(timestamp)) {
        timestampMap.set(timestamp, {
          time: timeLabel,
          sensors: {}
        });
      }
      
      timestampMap.get(timestamp).sensors[reading.sensor_type] = reading.value;
    });
    
    // Converter mapa para arrays ordenados
    const sortedEntries = Array.from(timestampMap.entries())
      .sort((a, b) => new Date(a[0]) - new Date(b[0]))
      .slice(-15); // Últimos 15 pontos
    
    // Extrair labels e dados
    sortedEntries.forEach(([timestamp, data]) => {
      timeLabels.push(data.time);
      sensorData.heart_rate.push(data.sensors.heart_rate || null);
      sensorData.blood_pressure.push(data.sensors.blood_pressure || null);
      sensorData.oxygen_saturation.push(data.sensors.oxygen_saturation || null);
      sensorData.temperature.push(data.sensors.temperature || null);
      sensorData.gsr.push(data.sensors.gsr || null);
    });

    // Debug: Log dos dados processados
    console.log('Labels de tempo:', timeLabels);
    console.log('Dados dos sensores:', sensorData);

    const datasets = [
      {
        label: 'Freq. Cardíaca (bpm)',
        data: sensorData.heart_rate,
        borderColor: '#3066d3',
        backgroundColor: 'rgba(48, 102, 211, 0.1)',
        tension: 0.2,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Pressão (mmHg)',
        data: sensorData.blood_pressure,
        borderColor: '#e67e22',
        backgroundColor: 'rgba(230, 126, 34, 0.1)',
        tension: 0.2,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Oxigenação (%)',
        data: sensorData.oxygen_saturation,
        borderColor: '#27ae60',
        backgroundColor: 'rgba(39, 174, 96, 0.1)',
        tension: 0.2,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Temperatura (°C)',
        data: sensorData.temperature,
        borderColor: '#c0392b',
        backgroundColor: 'rgba(192, 57, 43, 0.1)',
        tension: 0.2,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'GSR (Ω)',
        data: sensorData.gsr,
        borderColor: '#8e44ad',
        backgroundColor: 'rgba(142, 68, 173, 0.1)',
        tension: 0.2,
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6,
        yAxisID: 'y1', // Eixo secundário para GSR
      },
    ];

    const result = { labels: timeLabels, datasets };
    console.log('Resultado final do gráfico:', result);
    return result;
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 15
        }
      },
      title: {
        display: true,
        text: 'Sinais Vitais em Tempo Real',
        font: { size: 16, weight: 'bold' }
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Horário'
        }
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Valores (FC, PA, SpO2, Temp)'
        },
        min: 0,
        max: 180
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'GSR (Ω)'
        },
        min: 0,
        max: 1000,
        grid: {
          drawOnChartArea: false,
        },
      },
    },
    elements: {
      point: {
        radius: 4,
        hoverRadius: 8
      },
      line: {
        borderWidth: 3
      }
    },
    animation: {
      duration: 1000
    }
  };

  // Effects
  useEffect(() => {
    fetchLatestReadings();
    fetchVitalSigns();
    fetchAlerts();
    fetchProfile();
    checkESP32Status();

    // Atualizar dados a cada 5 segundos
    const interval = setInterval(() => {
      fetchLatestReadings();
      fetchVitalSigns();
      checkESP32Status();
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchLatestReadings, fetchVitalSigns, fetchAlerts, fetchProfile, checkESP32Status]);

  // Render
  return (
    <div className={`App ${darkMode ? 'dark-mode' : ''}`}>
      {/* Header */}
      <header className="site-header">
        <div className="brand">
          <div className="logo-box">VT</div>
          <div>
            <div className="site-title">VitalTech</div>
            <div className="site-subtitle">Sistema de monitoramento de sinais vitais</div>
          </div>
        </div>

        <div className="header-actions">
          <div className="esp32-status">
            <span className={`status-indicator ${esp32Connected ? 'connected' : 'disconnected'}`}>
              {esp32Connected ? '🟢 ESP32' : '🔴 Simulação'}
            </span>
          </div>
          <button 
            className="btn ghost" 
            onClick={toggleFullscreen}
            title={isFullscreen ? 'Sair da tela cheia' : 'Tela cheia'}
          >
            <i className={`fas fa-${isFullscreen ? 'compress' : 'expand'}`}></i>
          </button>
          <button 
            className="btn ghost" 
            onClick={() => setDarkMode(!darkMode)}
          >
            {darkMode ? 'Modo Claro' : 'Modo Escuro'}
          </button>
          <button className="btn" onClick={cleanupDemoData}>
            Limpar Dados
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main>
        {/* Sidebar */}
        <nav className="sidebar">
          <h2><i className="fas fa-heartbeat"></i> VitalTech</h2>
          {['Dashboard', 'Dados de Saúde', 'Alertas', 'Relatórios', 'Configurações'].map(section => (
            <button 
              key={section}
              onClick={() => setActiveSection(section)}
              className={activeSection === section ? 'active' : ''}
            >
              <i className={`fas fa-${
                section === 'Dashboard' ? 'chart-line' :
                section === 'Dados de Saúde' ? 'user' :
                section === 'Alertas' ? 'exclamation-triangle' :
                section === 'Relatórios' ? 'file-pdf' : 'cog'
              }`}></i>
              {section}
            </button>
          ))}
        </nav>

        {/* Content Area */}
        <section className="content">
          <div className="content-header">
            <h2>{activeSection}</h2>
            <div className="content-actions">
              {activeSection === 'Dashboard' && (
                <>
                  <button className="btn" onClick={runAIAnalysis} disabled={loading}>
                    <i className="fas fa-brain"></i> Análise IA
                  </button>
                  <button className="btn" onClick={() => generatePDFReport('daily')}>
                    <i className="fas fa-file-pdf"></i> Relatório
                  </button>
                  <button className="btn ghost" onClick={exportCSV}>
                    <i className="fas fa-file-csv"></i> Exportar CSV
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="cards">
            {/* Dashboard */}
            {activeSection === 'Dashboard' && (
              <div className="card dashboard-card">
                <h3>Medidas em tempo real</h3>
                
                {/* Chart */}
                <div className="chart-container">
                  <Line data={prepareChartData()} options={chartOptions} />
                </div>

                {/* Current Values */}
                <div className="vital-signs-grid">
                  <div className="vital-sign-item">
                    <div className="vital-sign-label">Freq. Cardíaca</div>
                    <div className="vital-sign-value">
                      {latestReadings.heart_rate?.value || '--'} bpm
                    </div>
                  </div>
                  <div className="vital-sign-item">
                    <div className="vital-sign-label">Pressão</div>
                    <div className="vital-sign-value">
                      {latestReadings.blood_pressure?.value || '--'} mmHg
                    </div>
                  </div>
                  <div className="vital-sign-item">
                    <div className="vital-sign-label">Oxigenação</div>
                    <div className="vital-sign-value">
                      {latestReadings.oxygen_saturation?.value || '--'} %
                    </div>
                  </div>
                  <div className="vital-sign-item">
                    <div className="vital-sign-label">Temperatura</div>
                    <div className="vital-sign-value">
                      {latestReadings.temperature?.value || '--'} °C
                    </div>
                  </div>
                  <div className="vital-sign-item">
                    <div className="vital-sign-label">Resistência Galvânica</div>
                    <div className="vital-sign-value">
                      {latestReadings.gsr?.value || '--'} Ω
                    </div>
                  </div>
                </div>

                {/* History Table */}
                <h4>Histórico (últimos 20 registros)</h4>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Hora</th>
                        <th>Sensor</th>
                        <th>Valor</th>
                        <th>Unidade</th>
                      </tr>
                    </thead>
                    <tbody>
                      {vitalSigns.slice(0, 20).map((reading, index) => (
                        <tr key={index}>
                          <td>{new Date(reading.timestamp).toLocaleTimeString('pt-BR')}</td>
                          <td>{reading.sensor_type}</td>
                          <td>{reading.value}</td>
                          <td>{reading.unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Dados de Saúde */}
            {activeSection === 'Dados de Saúde' && (
              <div className="card">
                <h3>Dados de Saúde</h3>
                <div className="profile-display">
                  <div className="patient-info">
                    <h4>Informações do Paciente</h4>
                    <div className="info-grid">
                      <div><strong>Nome:</strong> {profile.nome}</div>
                      <div><strong>Idade:</strong> {profile.idade || '--'} anos</div>
                      <div><strong>Sexo:</strong> {profile.genero || '--'}</div>
                      <div><strong>Altura:</strong> {profile.altura || '--'} cm</div>
                      <div><strong>Peso:</strong> {profile.peso || '--'} kg</div>
                      <div><strong>IMC:</strong> {calculateIMC()} ({getIMCClassification(calculateIMC())})</div>
                      <div><strong>Grupo Sanguíneo:</strong> {profile.grupo_sanguineo || '--'}</div>
                      <div><strong>Contato Emergência:</strong> {profile.contatos_emergencia || '--'}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Alertas */}
            {activeSection === 'Alertas' && (
              <div className="card">
                <h3>Alertas (IA)</h3>
                <div className="alerts-container">
                  {alerts.length === 0 ? (
                    <div className="no-alerts">Nenhum alerta registrado</div>
                  ) : (
                    alerts.map((alert, index) => (
                      <div key={index} className={`alert-item alert-${alert.level}`}>
                        <div className="alert-header">
                          <strong>{alert.title}</strong>
                        </div>
                        <div className="alert-message">{alert.message}</div>
                        <div className="alert-time">
                          {new Date(alert.timestamp).toLocaleString('pt-BR')}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Relatórios */}
            {activeSection === 'Relatórios' && (
              <div className="card">
                <h3>Relatórios</h3>
                <div className="reports-section">
                  <p>Selecione o período para gerar o relatório:</p>
                  <div className="report-buttons">
                    <button 
                      className="btn" 
                      onClick={() => generatePDFReport('daily')}
                      disabled={loading}
                    >
                      Relatório Diário
                    </button>
                    <button 
                      className="btn" 
                      onClick={() => generatePDFReport('weekly')}
                      disabled={loading}
                    >
                      Relatório Semanal
                    </button>
                    <button 
                      className="btn" 
                      onClick={() => generatePDFReport('monthly')}
                      disabled={loading}
                    >
                      Relatório Mensal
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Configurações */}
            {activeSection === 'Configurações' && (
              <div className="card">
                <h3>Configurações / Perfil</h3>
                <div className="profile-form">
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Nome completo</label>
                      <input
                        type="text"
                        value={profile.nome}
                        onChange={(e) => setProfile({...profile, nome: e.target.value})}
                        placeholder="Nome completo"
                      />
                    </div>
                    <div className="form-group">
                      <label>Idade</label>
                      <input
                        type="number"
                        value={profile.idade}
                        onChange={(e) => setProfile({...profile, idade: e.target.value})}
                        placeholder="Idade"
                      />
                    </div>
                    <div className="form-group">
                      <label>Sexo</label>
                      <input
                        type="text"
                        value={profile.genero}
                        onChange={(e) => setProfile({...profile, genero: e.target.value})}
                        placeholder="Sexo"
                      />
                    </div>
                    <div className="form-group">
                      <label>Altura (cm)</label>
                      <input
                        type="number"
                        value={profile.altura}
                        onChange={(e) => setProfile({...profile, altura: e.target.value})}
                        placeholder="Altura em cm"
                      />
                    </div>
                    <div className="form-group">
                      <label>Peso (kg)</label>
                      <input
                        type="number"
                        value={profile.peso}
                        onChange={(e) => setProfile({...profile, peso: e.target.value})}
                        placeholder="Peso em kg"
                      />
                    </div>
                    <div className="form-group">
                      <label>Grupo Sanguíneo</label>
                      <input
                        type="text"
                        value={profile.grupo_sanguineo}
                        onChange={(e) => setProfile({...profile, grupo_sanguineo: e.target.value})}
                        placeholder="Ex: O+, A-, B+..."
                      />
                    </div>
                    <div className="form-group">
                      <label>Telefone</label>
                      <input
                        type="text"
                        value={profile.telefone}
                        onChange={(e) => setProfile({...profile, telefone: e.target.value})}
                        placeholder="Telefone"
                      />
                    </div>
                    <div className="form-group">
                      <label>Email</label>
                      <input
                        type="email"
                        value={profile.email}
                        onChange={(e) => setProfile({...profile, email: e.target.value})}
                        placeholder="Email"
                      />
                    </div>
                  </div>

                  <div className="form-group full-width">
                    <label>Endereço</label>
                    <input
                      type="text"
                      value={profile.endereco}
                      onChange={(e) => setProfile({...profile, endereco: e.target.value})}
                      placeholder="Endereço completo"
                    />
                  </div>

                  <div className="form-group full-width">
                    <label>Condições Médicas</label>
                    <textarea
                      value={profile.condicoes_medicas}
                      onChange={(e) => setProfile({...profile, condicoes_medicas: e.target.value})}
                      placeholder="Condições médicas existentes"
                      rows="3"
                    />
                  </div>

                  <div className="form-group full-width">
                    <label>Alergias</label>
                    <textarea
                      value={profile.alergias}
                      onChange={(e) => setProfile({...profile, alergias: e.target.value})}
                      placeholder="Alergias conhecidas"
                      rows="2"
                    />
                  </div>

                  <div className="form-group full-width">
                    <label>Medicações</label>
                    <textarea
                      value={profile.medicacoes}
                      onChange={(e) => setProfile({...profile, medicacoes: e.target.value})}
                      placeholder="Medicações em uso"
                      rows="2"
                    />
                  </div>

                  <div className="form-group full-width">
                    <label>Contatos de Emergência</label>
                    <textarea
                      value={profile.contatos_emergencia}
                      onChange={(e) => setProfile({...profile, contatos_emergencia: e.target.value})}
                      placeholder="Contatos de emergência"
                      rows="2"
                    />
                  </div>

                  <div className="form-actions">
                    <button 
                      className="btn" 
                      onClick={saveProfile}
                      disabled={loading}
                    >
                      {loading ? 'Salvando...' : 'Salvar Perfil'}
                    </button>
                    <button 
                      className="btn ghost" 
                      onClick={fillSampleData}
                    >
                      Preencher Exemplo
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Loading Overlay */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
        </div>
      )}
    </div>
  );
}

export default App;