"""
Rotas para análises dos bots individuais
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

bot_analysis_bp = Blueprint('bot_analysis', __name__)
logger = logging.getLogger(__name__)

# Armazenar últimas análises em memória (por bot)
recent_analyses_cache = {}


def add_analysis_to_cache(bot_id, analysis):
    """Adiciona análise ao cache em memória"""
    if bot_id not in recent_analyses_cache:
        recent_analyses_cache[bot_id] = []
    
    recent_analyses_cache[bot_id].append(analysis)
    
    # Manter apenas últimas 20 análises por bot
    if len(recent_analyses_cache[bot_id]) > 20:
        recent_analyses_cache[bot_id] = recent_analyses_cache[bot_id][-20:]


@bot_analysis_bp.route('/bots/analyses/live', methods=['GET'])
def get_live_analyses():
    """
    Obtém análises em tempo real (apenas da memória, sem banco de dados)
    """
    try:
        from services.bot_manager_service import bot_manager
        
        # Obter todos os bots ativos
        bots = bot_manager.get_all_bots()
        active_bots = [b for b in bots if b.get('is_running')]
        
        if not active_bots:
            return jsonify({
                'success': True,
                'analyses': [],
                'total': 0,
                'timestamp': datetime.now().isoformat()
            })
        
        # Coletar análises do cache
        all_analyses = []
        
        for bot_data in active_bots:
            bot_id = bot_data.get('bot_id')
            
            if bot_id in recent_analyses_cache:
                bot_analyses = recent_analyses_cache[bot_id]
                all_analyses.extend(bot_analyses)
        
        # Ordenar por timestamp (mais recente primeiro)
        all_analyses.sort(
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Limitar a 30 análises
        all_analyses = all_analyses[:30]
        
        return jsonify({
            'success': True,
            'analyses': all_analyses,
            'total': len(all_analyses),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter análises live: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_analysis_bp.route('/bots/analyses', methods=['GET'])
def get_bots_analyses():
    """
    Obtém análises MLP de todos os bots ativos
    """
    try:
        from services.bot_manager_service import bot_manager
        
        # Obter todos os bots
        bots = bot_manager.get_all_bots()
        
        # Coletar análises de cada bot ativo
        all_analyses = []
        
        for bot_data in bots:
            if not bot_data.get('is_running'):
                continue  # Pular bots parados
            
            bot_id = bot_data.get('bot_id')
            symbol = bot_data.get('config', {}).get('symbol')
            
            if not symbol:
                continue
            
            # Obter bot instance
            bot = bot_manager.get_bot(bot_id)
            if not bot:
                continue
            
            try:
                # Tentar obter análises do trading engine do bot
                # Aqui você pode adicionar lógica para buscar análises específicas do bot
                # Por enquanto, vamos buscar do storage filtrando por símbolo
                
                from services.mlp_storage import mlp_storage
                
                # Buscar análises do símbolo específico
                # Buscar mais análises para garantir intercalação
                symbol_analyses = mlp_storage.get_analyses(
                    symbol=symbol,
                    limit=50  # Buscar mais para ter pool maior
                )
                
                # Adicionar bot_id a cada análise
                for analysis in symbol_analyses:
                    analysis['bot_id'] = bot_id
                    all_analyses.append(analysis)
                    
            except Exception as e:
                logger.error(f"Erro ao obter análises do bot {bot_id}: {e}")
                continue
        
        # Log para debug
        logger.info(f"Total de análises coletadas: {len(all_analyses)}")
        if all_analyses:
            symbols_count = {}
            for a in all_analyses:
                sym = a.get('symbol', 'N/A')
                symbols_count[sym] = symbols_count.get(sym, 0) + 1
            logger.info(f"Análises por símbolo: {symbols_count}")
        
        # Ordenar por timestamp (mais recente primeiro)
        all_analyses.sort(
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Log após ordenação
        if len(all_analyses) > 5:
            logger.info(f"Primeiras 5 análises após ordenação:")
            for i, a in enumerate(all_analyses[:5]):
                logger.info(f"  {i+1}. {a.get('timestamp')} - {a.get('symbol')} - {a.get('signal')}")
        
        # Limitar a 30 análises mais recentes (para melhor intercalação)
        all_analyses = all_analyses[:30]
        
        return jsonify({
            'success': True,
            'analyses': all_analyses,
            'total': len(all_analyses),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter análises dos bots: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
