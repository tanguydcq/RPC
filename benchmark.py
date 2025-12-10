#!/usr/bin/env python3
import os, sys, time, subprocess, pandas as pd, matplotlib.pyplot as plt
from datetime import datetime

# Tableau des solveurs disponibles
solvers = {
    'naive': 'src/solver_ad-hoc/naive.py',
    'naive_local': 'src/solver_ad-hoc/naive_local.py',
    'random_start': 'src/solver_ad-hoc/random_start.py',
    'random_start_local': 'src/solver_ad-hoc/random_start_local.py',
    'cp_model': 'src/solver_generic/cp_model.py'
}

def run_benchmark(input_file):
    output_dir = f"benchmarking/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    print("=" * 60)
    print("BENCHMARK DES SOLVEURS RPC")
    print("=" * 60)
    print(f"Fichier d'entrée: {input_file}")
    print(f"Nombre de solveurs: {len(solvers)}")
    print("=" * 60)
    
    for name, path in solvers.items():
        if os.path.exists(path):
            print(f"🔄 Exécution de {name:<20}... ", end="", flush=True)
            output_file = f"{output_dir}/{name}.txt"
            
            try:
                start = time.time()
                with open(output_file, 'w') as out:
                    result = subprocess.run([sys.executable, path, input_file], stdout=out, 
                                          stderr=subprocess.DEVNULL, timeout=600)
                
                exec_time = time.time() - start
                
                # Compter les camions dans la sortie
                max_truck_id = -1
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                    if lines and lines[0].strip() == "SAT":
                        # Pour chaque ligne après "SAT", lire le numéro du camion (premier chiffre)
                        for line in lines[1:]:
                            line = line.strip()
                            if line:  # Ignorer les lignes vides
                                try:
                                    truck_id = int(line.split()[0])
                                    max_truck_id = max(max_truck_id, truck_id)
                                except (ValueError, IndexError):
                                    continue
                
                # Le nombre de camions est max_truck_id + 1 (numérotation à partir de 0)
                trucks = max_truck_id + 1 if max_truck_id >= 0 else 0
                
                print(f"✅ {exec_time:.3f}s - {trucks} camions")
                results.append({'solver': name, 'time': exec_time, 'trucks': trucks, 'status': 'Success'})
                
            except subprocess.TimeoutExpired:
                print("❌ Timeout (>600s)")
                results.append({'solver': name, 'time': None, 'trucks': None, 'status': 'Timeout'})
            except Exception as e:
                print(f"❌ Erreur: {str(e)[:50]}")
                results.append({'solver': name, 'time': None, 'trucks': None, 'status': 'Error'})
        else:
            print(f"❌ {name:<20} - Fichier non trouvé")
            results.append({'solver': name, 'time': None, 'trucks': None, 'status': 'Not found'})
    
    # Sauvegarde des résultats
    df_all = pd.DataFrame(results)
    df_all.to_csv(f"{output_dir}/results.csv", index=False)
    
    # Filtrer les résultats valides pour l'analyse
    df = df_all[df_all['status'] == 'Success'].copy()
    
    print("\n" + "=" * 60)
    print("RÉSULTATS COMPARATIFS")
    print("=" * 60)
    
    if not df.empty:
        # Trier par nombre de camions, puis par temps
        df_sorted = df.sort_values(['trucks', 'time'])
        
        print(f"{'Solveur':<20} {'Temps (s)':<12} {'Camions':<10} {'Statut'}")
        print("-" * 60)
        for _, row in df_all.iterrows():
            status_symbol = "✅" if row['status'] == 'Success' else "❌"
            time_str = f"{row['time']:.3f}" if row['time'] is not None else "N/A"
            trucks_str = str(row['trucks']) if row['trucks'] is not None else "N/A"
            print(f"{status_symbol} {row['solver']:<18} {time_str:<12} {trucks_str:<10} {row['status']}")
        
        print("\n" + "=" * 60)
        print("ANALYSE")
        print("=" * 60)
        
        if len(df) > 1:
            best_trucks = df.loc[df['trucks'].idxmin()]
            fastest = df.loc[df['time'].idxmin()]
            
            print(f"🏆 Meilleur solveur (moins de camions): {best_trucks['solver']} ({int(best_trucks['trucks'])} camions)")
            print(f"⚡ Solveur le plus rapide: {fastest['solver']} ({fastest['time']:.3f}s)")
            
            if best_trucks['solver'] != fastest['solver']:
                print(f"📊 Compromis: {best_trucks['solver']} vs {fastest['solver']}")
        
        # Graphiques
        if len(df) > 0:
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))
            
            # Graphique des temps
            df_plot = df.sort_values('time')
            axes[0].bar(range(len(df_plot)), df_plot['time'], color='skyblue')
            axes[0].set_xticks(range(len(df_plot)))
            axes[0].set_xticklabels(df_plot['solver'], rotation=45)
            axes[0].set_title('Temps d\'exécution (secondes)')
            axes[0].set_ylabel('Temps (s)')
            
            # Graphique des camions
            df_plot = df.sort_values('trucks')
            axes[1].bar(range(len(df_plot)), df_plot['trucks'], color='lightcoral')
            axes[1].set_xticks(range(len(df_plot)))
            axes[1].set_xticklabels(df_plot['solver'], rotation=45)
            axes[1].set_title('Nombre de camions utilisés')
            axes[1].set_ylabel('Camions')
            
            plt.tight_layout()
            plt.savefig(f"{output_dir}/comparison.png", dpi=150, bbox_inches='tight')
            plt.show()
    
    else:
        print("❌ Aucun solveur n'a fonctionné correctement")
    
    print(f"\n📁 Résultats sauvegardés dans: {output_dir}")
    return df_all

if __name__ == "__main__":
    if len(sys.argv) != 2: print("Usage: python benchmark.py <input_file>"); sys.exit(1)
    run_benchmark(sys.argv[1])