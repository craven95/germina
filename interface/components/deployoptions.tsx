'use client'

import { useState } from 'react'

interface DeployOptionsProps {
  image: { name: string }
  onClose: () => void
}

const DeployOptions = ({ image, onClose }: DeployOptionsProps) => {
  const [deployType, setDeployType] = useState<'local' | 'vm'>('local')
  const [osType, setOsType] = useState<'linux' | 'mac' | 'windows'>('linux')
  const [vmConfig, setVmConfig] = useState({
    ip: '',
    user: 'ubuntu',
    key: '',
    port: 22,
  })
  const builderApiUrl = process.env.NEXT_PUBLIC_BUILDER_API_URL || 'http://localhost:8000';

  const handleDeploy = async () => {
    try {
      if (deployType === 'local') {
        console.log('Déploiement LOCAL sur', osType)
        const res = await fetch(`${builderApiUrl}/generate_deploy_script`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image: image.name,
            os: osType,
            port: 5000,
            qid: image.name,
          }),
        })

        const script = await res.text()
        const blob = new Blob([script], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `deploy_${image.name}_${osType}.${osType === 'windows' ? 'ps1' : 'sh'}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
      } else {
        await fetch('${builderApiUrl}/deploy-remote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            image: image.name,
            ...vmConfig,
          }),
        })
      }
      onClose()
    } catch (e: any) {
      alert(`Erreur: ${e.message}`)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-md w-full">
        <h3 className="text-xl font-bold mb-4">Options de déploiement</h3>

        <select
          value={deployType}
          onChange={(e) => setDeployType(e.target.value as 'local' | 'vm')}
          className="mb-4 p-2 border rounded w-full"
        >
          <option value="local">Sur mon PC</option>
          <option value="vm">Sur une VM distante</option>
        </select>

        {deployType === 'local' && (
          <div>
            <label className="block mb-1">Système d'exploitation :</label>
            <select
              value={osType}
              onChange={(e) => setOsType(e.target.value as 'linux' | 'mac' | 'windows')}
              className="p-2 border rounded w-full mb-4"
            >
              <option value="linux">Linux</option>
              <option value="mac">macOS</option>
              <option value="windows">Windows</option>
            </select>
          </div>
        )}

        {deployType === 'vm' && (
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Adresse IP de la VM"
              value={vmConfig.ip}
              onChange={(e) => setVmConfig({ ...vmConfig, ip: e.target.value })}
              className="p-2 border rounded w-full"
            />
            <input
              type="text"
              placeholder="Utilisateur SSH"
              value={vmConfig.user}
              onChange={(e) => setVmConfig({ ...vmConfig, user: e.target.value })}
              className="p-2 border rounded w-full"
            />
            <input
              type="number"
              placeholder="Port SSH (défaut 22)"
              value={vmConfig.port}
              onChange={(e) => setVmConfig({ ...vmConfig, port: Number(e.target.value) })}
              className="p-2 border rounded w-full"
            />
            <textarea
              placeholder="Clé privée SSH"
              value={vmConfig.key}
              onChange={(e) => setVmConfig({ ...vmConfig, key: e.target.value })}
              className="p-2 border rounded w-full h-32"
            />
          </div>
        )}

        <div className="flex gap-2 mt-4">
          <button
            onClick={handleDeploy}
            className="bg-green-600 text-white px-4 py-2 rounded"
          >
            Déployer
          </button>
          <button
            onClick={onClose}
            className="bg-gray-600 text-white px-4 py-2 rounded"
          >
            Annuler
          </button>
        </div>
      </div>
    </div>
  )
}

export default DeployOptions
