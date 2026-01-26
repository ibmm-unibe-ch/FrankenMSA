from copy import deepcopy
import re
import os
import httpx
import logging


# adopted from https://github.com/boscoh/uniprot

def is_html(text):
  if re.search('<html', text):
    return True
  return False

def fetch_uniprot_metadata(seqids, cache_fname=None):
  """
  Returns a dictonary of the uniprot metadata (as parsed
  by parse_uniprot_txt_file) of the given seqids. The seqids
  must be valid uniprot identifiers.

  Now handles isoform versions of accession id's!
  """

  primary_seqids = [s for s in seqids] # changed from https://github.com/boscoh/uniprot
  if cache_fname and os.path.isfile(cache_fname):
    logging("Loading cached metadata from " + cache_fname + "\n")
    cache_txt = open(cache_fname).read()
  else:
    logging("Fetching metadata for %d Uniprot IDs from UniProt ...\n" % len(primary_seqids))
    client = httpx.Client(timeout=30.0)
    try:
      r = client.post(
          'https://rest.uniprot.org/uniprotkb/search',
          params={
            'query': ' OR '.join(['accession:%s' % s for s in primary_seqids]),
            'format': 'txt'
          })
      
      if r.status_code == 200:
        cache_txt = r.text
      else:
        logging("Error fetching metadata: HTTP %d\n" % r.status_code)
        return {}
      
      if cache_fname:
        with open(cache_fname, 'w') as f:
          f.write(cache_txt)
      
      if is_html(cache_txt):
        # Got HTML response -> error
        logging("Error in fetching metadata\n")
        return {}
    finally:
      client.close()
  logging(f"cache_txt {cache_txt}")
  return parse_uniprot_metadata_with_seqids(seqids, cache_txt)

def parse_uniprot_metadata_with_seqids(seqids, cache_txt):
  """
  Returns a dictionary of metadata of given seqids, doing the requisite
  lookup of seqids in the ACCs and IDs, and more importantly handles
  isoform seqid's
  """
  metadata = parse_uniprot_txt_file(cache_txt)
  logging(f"metadata {metadata.keys()}")
  logging(f"metadata {metadata}")
  tmp = metadata.copy()
  for uniprot_id in metadata.keys():
    for seqid in metadata[uniprot_id]['accs'] + [metadata[uniprot_id]['id']]:
      tmp[seqid] = metadata[uniprot_id]
  logging("asdfasdfasdfasdfdsfdsf\n")
  logging(f"tmp {tmp}")
  metadata = tmp
  results = {}
  isoform_dict = parse_isoforms(cache_txt)
  for seqid in seqids:
    if seqid in metadata:
      results[seqid] = metadata[seqid]
    else:
      primary_seqid = seqid[:6]
      if primary_seqid in metadata:
        protein_metadata = metadata[primary_seqid]
        uniprot_id = protein_metadata['id']
        if uniprot_id in isoform_dict:
          isoforms = isoform_dict[uniprot_id]['isoforms'].values()
          for isoform in isoforms:
            if isoform['seqid'] == seqid:
              results[seqid] = deepcopy(protein_metadata)
              results[seqid]['accs'] = [seqid]
              results[seqid]['sequence'] = isoform['sequence']
  return results

def parse_uniprot_txt_file(cache_txt):
  """
  Parses the text of metadata retrieved from uniprot.org.

  Only a few fields have been parsed, but this provides a
  template for the other fields.

  A single description is generated from joining alternative
  descriptions.

  Returns a dictionary with the main UNIPROT ACC as keys.
  """

  tag = None
  uniprot_id = None
  metadata_by_seqid = {}
  for l in cache_txt.splitlines():
    test_tag = l[:5].strip()
    if test_tag and test_tag != tag:
      tag = test_tag
    line = l[5:].strip()
    words = line.split()
    if tag == "ID":
      uniprot_id = words[0]
      is_reviewed = words[1].startswith('Reviewed')
      length = int(words[2])
      metadata_by_seqid[uniprot_id] = {
        'id': uniprot_id,
        'is_reviewed': is_reviewed,
        'length': length,
        'sequence': '',
        'accs': [],
      }
      entry = metadata_by_seqid[uniprot_id]
    if tag == "SQ":
      if words[0] != "SEQUENCE":
        entry['sequence'] += ''.join(words)
    if tag == "AC":
      accs = [w.replace(";", "") for w in words]
      entry['accs'].extend(accs)
    if tag == "DR":
      if 'PDB' in words[0]:
        if 'pdb' not in entry:
          entry['pdb'] = words[1][:-1]
        if 'pdbs' not in entry:
          entry['pdbs'] = []
        entry['pdbs'].append(words[1][:-1])
      if 'RefSeq' in words[0]:
        if 'refseq' not in entry:
          entry['refseq'] = []
        ids = [w[:-1] for w in words[1:]]
        entry['refseq'].extend(ids)
      if 'KEGG' in words[0]:
        if 'kegg' not in entry:
          entry['kegg'] = []
        ids = [w[:-1] for w in words[1:]]
        ids = list(filter(lambda w: len(w) > 1, ids))
        entry['kegg'].extend(ids)
      if 'GO' in words[0]:
        if 'go' not in entry:
          entry['go'] = []
        entry['go'].append(' '.join(words[1:]))
      if 'Pfam' in words[0]:
        if 'pfam' not in entry:
          entry['pfam'] = []
        entry['pfam'].append(words[1][:-1])
    if tag == "GN":
      if 'gene' not in entry and len(words) > 0:
        pieces = words[0].split("=")
        if len(pieces) > 1 and 'name' in pieces[0].lower():
          entry['gene'] = pieces[1].replace(';', '').replace(',', '')
    if tag == "OS":
      if 'organism' not in entry:
        entry['organism'] = ""
      entry['organism'] += line
    if tag == "DE":
      if 'descriptions' not in entry:
        entry['descriptions'] = []
      entry['descriptions'].append(line)
    if tag == "CC":
      if 'comment' not in entry:
        entry['comment'] = ''
      entry['comment'] += line + '\n'

  for entry in metadata_by_seqid.values():
    descriptions = entry['descriptions']
    for i in reversed(range(len(descriptions))):
      description = descriptions[i]
      if 'Short' in description or 'Full' in description:
        j = description.find('=')
        descriptions[i] = description[j+1:].replace(';', '')
      else:
        del descriptions[i]
    entry['description'] = '; '.join(descriptions)

  return metadata_by_seqid

def parse_isoforms(text):
  """
  Returns a dictionary of uniprot_acc and entries.

  Each entry contains:
    - var_seq: the sequence variations in the file
    - isoforms: the interpreted isoform sequences with
                the seqids
  """
  tag = None
  uniprot_data = {}
  var_seq = None
  in_isoform_section = False
  isoform_id = None
  for l in text.splitlines():
    test_tag = l[:5].strip()
    if test_tag and test_tag != tag:
      tag = test_tag
    line = l[5:].strip()
    words = line.split()
    if tag == "ID":
      uniprot_id = words[0]
      uniprot_data[uniprot_id] = {
        'var_seqs': [],
        'isoforms': {},
        'sequence': '',
      }
    if tag == "SQ":
      if words[0] != "SEQUENCE":
        uniprot_data[uniprot_id]['sequence'] += ''.join(words)
    if tag == 'FT':
      if var_seq is not None and l[5] != ' ':
        var_seq = None
      if line.startswith('VAR_SEQ'):
        range_str = words[1]
        if '..' in range_str:
          parts = range_str.split('..')
          var_seq = {
            'i': int(parts[0]),
            'j': int(parts[1]),
            'block': ''
          }
        elif len(words) >= 3 and words[2].isdigit():
          var_seq = {
            'i': int(words[1]),
            'j': int(words[2]),
            'block': ''
          }
        else:
          pos = int(words[1])
          var_seq = {
            'i': pos,
            'j': pos,
            'block': ''
          }
        uniprot_data[uniprot_id]['var_seqs'].append(var_seq)
      if var_seq is not None:
        var_seq['block'] += l[34:]
        if l.endswith('isoform'):
          # needed later to search isoform references
          var_seq['block'] += ' '
    if tag == 'CC':
      if words[0] == '-!-':
        if 'ALTERNATIVE' in words[1] and 'PRODUCTS' in words[2]:
          in_isoform_section = True
        else:
          in_isoform_section = False
      if in_isoform_section:
        if words[0].startswith('Name'):
          isoform_id = str(words[0][:-1].split('=')[1])
        for word in words:
          if word.startswith('IsoId='):
            seqid = word[:-1].split('=')[1]
            uniprot_data[uniprot_id]['isoforms'][isoform_id] = {
              'seqid': seqid
            }
            break
  for uniprot_id in uniprot_data:
    var_seqs = uniprot_data[uniprot_id]['var_seqs']
    isoforms = uniprot_data[uniprot_id]['isoforms']
    original_sequence = uniprot_data[uniprot_id]['sequence']
    for var_seq in var_seqs:
      block = var_seq['block']
      match = re.search(r'\(.*\)', block)
      isoform_ids = []
      if match:
        isoform_tokens = match.group()[1:-1].split()
        for i in range(len(isoform_tokens)):
          if 'isoform' in isoform_tokens[i]:
            isoform_ids.append(str(isoform_tokens[i+1]))
      var_seq['isoform_ids'] = isoform_ids
      if block.startswith('Missing'):
        var_seq['deletion'] = True
      else:
        var_seq['deletion'] = False
        transition = block.split('(')[0]
        if '->' in transition:
          original, mutation = transition.split('->')
          var_seq['sequence'] = original.strip()
          var_seq['mutation'] = mutation.strip()
        else:
          var_seq['sequence'] = ''
          var_seq['mutation'] = transition.strip()
    var_seqs.sort(key=lambda v:-v['i'])
    for isoform_id in isoforms:
      sequence = original_sequence
      for var_seq in uniprot_data[uniprot_id]['var_seqs']:
        if isoform_id in var_seq['isoform_ids']:
          i = var_seq['i']-1
          j = var_seq['j']
          if var_seq['deletion']:
            sequence = sequence[:i] + sequence[j:]
          else:
            sequence = sequence[:i] + var_seq['mutation'] + sequence[j:]
      isoforms[isoform_id]['sequence'] = sequence
  return uniprot_data