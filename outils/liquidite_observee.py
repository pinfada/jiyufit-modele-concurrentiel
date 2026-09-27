"""Mesurer la liquidité à partir de recherches, y compris celles sans résultat."""
import csv
from datetime import datetime
import math


def mesurer(path):
    required={'recherche_id','horodatage','territoire','seances_compatibles_disponibles','reservation_confirmee'}
    with open(path,encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if not required.issubset(reader.fieldnames or []) or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError('Colonnes de recherches manquantes ou dupliquées')
        rows=list(reader)
    if not rows: raise ValueError('Aucune recherche observée : liquidité inconnue')
    seen, groups=set(),{}
    for row in rows:
        key=row['recherche_id']
        if not key or not key.strip() or key in seen or None in row or any(row[k] is None for k in required):
            raise ValueError('Recherche absente, dupliquée ou ligne mal formée')
        seen.add(key)
        time=datetime.fromisoformat(row['horodatage'].replace('Z','+00:00'))
        if time.utcoffset() is None: raise ValueError('Fuseau horaire obligatoire')
        if not row['territoire'].strip(): raise ValueError('Territoire obligatoire')
        if not row['seances_compatibles_disponibles'].isdigit(): raise ValueError('Nombre de séances entier non négatif requis')
        available=int(row['seances_compatibles_disponibles'])
        if row['reservation_confirmee'] not in ('0','1'): raise ValueError('Confirmation 0/1 requise')
        booked=int(row['reservation_confirmee'])
        if booked and available==0: raise ValueError('Réservation incompatible avec zéro offre disponible')
        g=groups.setdefault((row['territoire'],time.strftime('%Y-%m')), [0,0,0])
        g[0]+=1; g[1]+=int(available>0); g[2]+=booked
    result=[]
    for (territory,month),(n,k,b) in sorted(groups.items()):
        p=k/n; z=1.96; den=1+z*z/n
        center=(p+z*z/(2*n))/den
        radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
        result.append(dict(territoire=territory,mois=month,recherches=n,
                           liquidite=k/n,conversion_reservation=b/n,
                           intervalle_wilson95_iid=[max(0,center-radius),min(1,center+radius)],
                           limite='Intervalle indicatif ; répétitions utilisateurs et dépendance temporelle non corrigées'))
    return result
